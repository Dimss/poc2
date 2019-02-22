import unittest
import HtmlTestRunner
import os
import conf


class TestExample(unittest.TestCase):

    def test_config_env_var_rabbitmq_ip(self):
        self.assertEqual(os.getenv('PROFILE', 'dev'), conf.PROFILE)

    def test_config_env_var_rabbitmq_ip(self):
        self.assertEqual(os.getenv('RABBITMQ_IP', '127.0.0.1'), conf.RABBITMQ_IP)

    def test_config_env_var_rabbitmq_queue(self):
        self.assertEqual(os.getenv('RABBITMQ_QUEUE', 'sites'), conf.RABBITMQ_QUEUE)


if __name__ == '__main__':
    print("This is main")
    unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output=''))
