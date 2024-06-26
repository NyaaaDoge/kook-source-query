import logging
import os

from logging import Logger
from logging.handlers import TimedRotatingFileHandler

from khl import Message, Event


class BotLogger(object):
    def __init__(self, logger: Logger):
        self.logger = logger

    def logging_public_msg(self, msg: Message):
        """
        记录消息日志
        :param msg:
        :return:
        """
        self.logger.info(f"Message: G_id({msg.ctx.guild.id})-C_id({msg.ctx.channel.id}) - "
                         f"Au({msg.author_id})-({msg.author.username}#{msg.author.identify_num}) = {msg.content}")

    def logging_normal_event(self, event: Event):
        """
        记录事件日志
        :param event:
        :return:
        """
        self.logger.info(f"Event: G_id({event.body['guild_id']})-C_id({event.body['target_id']}) - "
                         f"Au({event.body['user_id']})-"
                         f"({event.body['user_info']['username']}#{event.body['user_info']['identify_num']})"
                         f" = Type({event.event_type})-Body_val({event.body['value']})")

    def create_log_file(self, filename: str):
        """
        将日志记录到日志文件
        :param filename: ./logs/filename
        :return:
        """
        filename = './logs/' + filename

        try:
            # 尝试创建 FileHandler
            fh = logging.FileHandler(filename=filename, encoding='utf-8', mode='a')

        except OSError:
            os.makedirs(os.path.dirname(filename))
            # 再次尝试创建 FileHandler
            fh = logging.FileHandler(filename=filename, encoding="utf-8", mode="a")

        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        return self.logger

    def create_log_file_by_rotate_handler(self, filename: str):
        filename = './logs/' + filename
        try:
            # 尝试创建 RotatingFileHandler
            fh = TimedRotatingFileHandler(filename, when='D', interval=1, backupCount=7)
            # 设置日志文件的命名规则，按天切分日志文件
            # 'when'参数可以是 'S'、'M'、'H'、'D'、'W0'-'W6'，分别表示秒、分钟、小时、天、周一到周日切分
            # 'interval'参数表示切分的时间间隔
            # 'backupCount'参数表示保留的日志文件的最大数量

        except OSError:
            os.makedirs(os.path.dirname(filename))
            # 再次尝试创建 RotatingFileHandler
            fh = TimedRotatingFileHandler(filename, when='D', interval=1, backupCount=7)

        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s -%(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
