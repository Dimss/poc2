import groovy.json.JsonOutput

def getJobName() {
    def jobNameList = env.JOB_NAME.split("/")
    if (jobNameList.size() > 0) {
        return jobNameList[jobNameList.size() - 1]
    } else {
        return jobName
    }
}

def getAppName() {
    if (env.gitlabActionType == "TAG_PUSH") {
        return "${getJobName()}-${getGitTag()}"
    } else {
        return "${getJobName()}-${getGitCommitShortHash()}"
    }
}

def getGitCommitShortHash() {
    return checkout(scm).GIT_COMMIT.substring(0, 7)
}

def getGitTag() {
    if (env.gitlabActionType == "TAG_PUSH") {
        def tagPathList = env.gitlabSourceBranch.split("/")
        return tagPathList[tagPathList.size() - 1]
    } else {
        return ""
    }
}

def getProfile(){
    if (env.gitlabActionType == "TAG_PUSH") {
        return "lab"
    } else {
        return "dev"
    }
}

def getDockerImageTag() {
    if (env.gitlabActionType == "TAG_PUSH") {
        return getGitTag()
    } else {
        return "${getGitCommitShortHash()}-${currentBuild.number}"
    }
}

def deployPoc12Dependency(){
    openshift.withCluster() {
        openshift.withProject() {
            def poc12dep = openshift.selector("poc12dep")
            if (poc12dep.exists()){
                echo "Dependency for Poc1Producer and Poc2Consumer already exists, gonna skip Pod12Dep creation"
                return
            }
            def crDepTemplate = readFile('ocp/cd/cr-dep-template.yaml')
            def appName = "poc12-rabbitmq-dev"
            def profile = getProfile()
            def image = "docker.io/rabbitmq:3-management"
            def namespace = openshift.project()
            def routeHostSuffix = "router.default.svc.cluster.local"
            def queueName = "sites"

            def models = openshift.process(crDepTemplate,
                    "-p=APP_NAME=${appName}",
                    "-p=NAMESPACE=${namespace}",
                    "-p=IMAGE=${image}",
                    "-p=ROUTE_HOST_SUFFIX=${routeHostSuffix}",
                    "-p=QUEUE_NAME=${queueName}",
                    "-p=PROFILE=${profile}")
            echo "${JsonOutput.prettyPrint(JsonOutput.toJson(models))}"
            openshift.create(models)
        }
    }
}

def deployPoc2Consumer(){
    openshift.withCluster() {
        openshift.withProject() {
            def size = 1
            def appName = getAppName()
            def namespace = openshift.project()
            def image = "${env.DOCKER_REGISTRY}/${env.DOCKER_IMAGE_PREFIX}/${GOVIL_APP_NAME}:${getDockerImageTag()}"
            def profile = getProfile()
            def crTemplate = readFile('ocp/cd/cr-app-template.yaml')
            def models = openshift.process(crTemplate,
                    "-p=SIZE=${size}",
                    "-p=APP_NAME=${appName}",
                    "-p=NAMESPACE=${namespace}",
                    "-p=IMAGE=${image}",
                    "-p=PROFILE=${profile}")
            echo "${JsonOutput.prettyPrint(JsonOutput.toJson(models))}"
            openshift.create(models)
        }
    }

}

pipeline {
    agent {
        node {
            label 'python36'
        }
    }
    stages {
        stage('Checkout GIT Tag (in case it was pushed) ') {

            steps {
                script {
                    if (env.gitlabActionType == "TAG_PUSH") {
                        checkout poll: false, scm: [
                                $class                           : 'GitSCM',
                                branches                         : [[name: "${env.gitlabSourceBranch}"]],
                                doGenerateSubmoduleConfigurations: false,
                                submoduleCfg                     : [],
                        ]
                    }
                }
            }
        }
        stage("Install PIP dependencies") {
            steps {
                script {
                    sh "pipenv install"
                }
            }
        }
        stage("Deploy tests infra dependencies") {
            steps {
                script {
                    openshift.withCluster() {
                        openshift.withProject() {
                            def testDepTemplate = readFile('ocp/ci/unittests-resources-template.yaml')
                            env.shortCommit = checkout(scm).GIT_COMMIT.substring(0, 7)
                            env.rabbitmqName = "rabbitmq-${env.shortCommit}"
                            def models = openshift.process(testDepTemplate, "-p=RABBITMQ_NAME=${rabbitmqName}")
                            openshift.create(models)
                            def deployment = openshift.selector("deployment/${rabbitmqName}")
                            deployment.untilEach(1) {
                                echo "${it.object()}"
                                return it.object().status.readyReplicas == 1
                            }
                            echo "${deployment}"
                            echo "${models}"
                            echo "${env.shortCommit}"
                            echo "${currentBuild.number}"

                        }
                    }

                }
            }
        }
        stage("Run tests") {
            steps {
                script {
                    sh """
                        echo PROFILE=prod >.env
                        echo RABBITMQ_IP="${env.rabbitmqName}" >>.env
                        echo RABBITMQ_QUEUE="sites-${env.shortCommit}" >>.env
                        pipenv run test
                    """
                }
            }
        }

        stage("Cleanup test resources") {
            steps {
                script {
                    openshift.withCluster() {
                        openshift.withProject() {
                            def testDepTemplate = readFile('ocp/ci/unittests-resources-template.yaml')
                            def models = openshift.process(testDepTemplate, "-p=RABBITMQ_NAME=${env.rabbitmqName}")
                            openshift.delete(models)
                        }
                    }
                }
            }
        }

        stage("Create S2I image stream and build configs") {
            steps {
                script {
                    openshift.withCluster() {
                        openshift.withProject() {
                            def icBcTemplate = readFile('ocp/ci/app-is-bc.yaml')
                            def models = openshift.process(icBcTemplate,
                                    "-p=BC_IS_NAME=${getAppName()}",
                                    "-p=DOCKER_REGISTRY=${env.DOCKER_REGISTRY}",
                                    "-p=DOCKER_IMAGE_NAME=/${env.DOCKER_IMAGE_PREFIX}/${GOVIL_APP_NAME}",
                                    "-p=DOCKER_IMAGE_TAG=${getDockerImageTag()}",
                                    "-p=GIT_REPO=${scm.getUserRemoteConfigs()[0].getUrl()}",
                                    "-p=GIT_REF=${env.gitlabSourceBranch}",
                                    "-p=S2I_BUILDER_ISTAG=${env.S2I_BUILD_IMAGE}"
                            )
                            echo "${JsonOutput.prettyPrint(JsonOutput.toJson(models))}"
                            openshift.create(models)
                            def bc = openshift.selector("buildconfig/${getAppName()}")
                            def build = bc.startBuild()
                            build.logs("-f")
                            openshift.delete(models)
                        }
                    }
                }
            }
        }

        stage("Deploy to OpenShift") {
            steps {
                script {
                    openshift.withCluster() {
                        openshift.withProject() {
                            deployPoc12Dependency()

                            deployPoc2Consumer()
                        }
                    }
                }
            }
        }
    }


    post {
        failure {
            script {
                openshift.withCluster() {
                    openshift.withProject() {
                        def testDepTemplate = readFile('ocp/ci/unittests-resources-template.yaml')
                        def models = openshift.process(testDepTemplate, "-p=RABBITMQ_NAME=${env.rabbitmqName}")
                        openshift.delete(models)

                    }
                }
            }
        }
    }
}