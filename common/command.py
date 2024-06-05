class CommandBase(type):
    registry = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        if cls.__name__ not in cls.registry:
            cls.registry[attrs["name"]] = cls

    @classmethod
    def add_parser(cls, parser):
        """
        添加命令行参数

        Args:
            parser (argparse.ArgumentParser):

        Returns:

        """
        # 可选行为，因此不抛出NotImplementedError
        ...

    @classmethod
    def run(cls, params):
        """
        运行命令

        Args:
            params (dict[str, str]): key就是在add_parser中定义的参数名

        Returns:

        """
        raise NotImplementedError
