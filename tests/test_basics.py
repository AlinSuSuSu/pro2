import unittest
from flask import current_app
from app import create_app, db

#以test_开头的函数都作为测试执行


class BasicTestCase(unittest.TestCase):
    #创建一个测试环境
    def setUp(self):
        # 测试配置创建程序，激活上下文
        self.app = create_app('testing')
        self.app_context=self.app.app_context()
        self.app_context.push()
        db.create_all()#创建数据库，以备不时之需

    #删除setUp函数中创建的数据库和程序上下文
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    #测试 确保程序实例存在
    def test_app_exists(self):
        self.assertFalse(current_app is None)
    #测试 确保程序在测试配置中运行
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])

