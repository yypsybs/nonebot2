#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path
from datetime import timedelta
from ipaddress import IPv4Address

from pydantic import BaseSettings, IPvAnyAddress
from pydantic.env_settings import SettingsError, env_file_sentinel, read_env_file

from nonebot.typing import Any, Set, Dict, Union, Mapping, Optional


class BaseConfig(BaseSettings):

    def _build_environ(
            self,
            _env_file: Union[Path, str, None] = None,
            _env_file_encoding: Optional[str] = None
    ) -> Dict[str, Optional[str]]:
        """
        Build environment variables suitable for passing to the Model.
        """
        d: Dict[str, Optional[str]] = {}

        if self.__config__.case_sensitive:
            env_vars: Mapping[str, Optional[str]] = os.environ
        else:
            env_vars = {k.lower(): v for k, v in os.environ.items()}

        env_file_vars: Dict[str, Optional[str]] = {}
        env_file = _env_file if _env_file != env_file_sentinel else self.__config__.env_file
        env_file_encoding = _env_file_encoding if _env_file_encoding is not None else self.__config__.env_file_encoding
        if env_file is not None:
            env_path = Path(env_file)
            if env_path.is_file():
                env_file_vars = read_env_file(
                    env_path,
                    encoding=env_file_encoding,
                    case_sensitive=self.__config__.case_sensitive)
                env_vars = {**env_file_vars, **env_vars}

        for field in self.__fields__.values():
            env_val: Optional[str] = None
            for env_name in field.field_info.extra['env_names']:
                env_val = env_vars.get(env_name)
                if env_name in env_file_vars:
                    del env_file_vars[env_name]
                if env_val is not None:
                    break

            if env_val is None:
                continue

            if field.is_complex():
                try:
                    env_val = self.__config__.json_loads(env_val)
                except ValueError as e:
                    raise SettingsError(
                        f'error parsing JSON for "{env_name}"'  # type: ignore
                    ) from e
            d[field.alias] = env_val

        if env_file_vars:
            for env_name, env_val in env_file_vars.items():
                try:
                    env_val = self.__config__.json_loads(env_val)
                except ValueError as e:
                    pass

                d[env_name] = env_val

        return d

    def __getattr__(self, name: str) -> Any:
        return self.__dict__.get(name)


class Env(BaseSettings):
    """
    运行环境配置。大小写不敏感。

    将会从 ``nonebot.init 参数`` > ``环境变量`` > ``.env 环境配置文件`` 的优先级读取配置。
    """

    environment: str = "prod"
    """
    - 类型: ``str``
    - 默认值: ``"prod"``
    - 说明:
      当前环境名。 NoneBot 将从 ``.env.{environment}`` 文件中加载配置。
    """

    class Config:
        env_file = ".env"


class Config(BaseConfig):
    """
    NoneBot 主要配置。大小写不敏感。

    除了 NoneBot 的配置项外，还可以自行添加配置项到 ``.env.{environment}`` 文件中。这些配置将会一起带入 ``Config`` 类中。
    """
    # nonebot configs
    driver: str = "nonebot.drivers.fastapi"
    """
    - 类型: ``str``
    - 默认值: ``"nonebot.drivers.fastapi"``
    - 说明:
      NoneBot 运行所使用的 ``Driver`` 。继承自 ``nonebot.driver.BaseDriver`` 。
    """
    host: IPvAnyAddress = IPv4Address("127.0.0.1")  # type: ignore
    """
    - 类型: ``IPvAnyAddress``
    - 默认值: ``127.0.0.1``
    - 说明:
      NoneBot 的 HTTP 和 WebSocket 服务端监听的 IP／主机名。
    """
    port: int = 8080
    """
    - 类型: ``int``
    - 默认值: ``8080``
    - 说明:
      NoneBot 的 HTTP 和 WebSocket 服务端监听的端口。
    """
    secret: Optional[str] = None
    """
    - 类型: ``Optional[str]``
    - 默认值: ``None``
    - 说明:
      上报连接 NoneBot 所需的密钥。
    - 示例:

    .. code-block:: http

        POST /cqhttp/ HTTP/1.1
        Authorization: Bearer kSLuTF2GC2Q4q4ugm3
    """
    debug: bool = False
    """
    - 类型: ``bool``
    - 默认值: ``False``
    - 说明:
      是否以调试模式运行 NoneBot。
    """

    # bot connection configs
    api_root: Dict[str, str] = {}
    api_timeout: Optional[float] = 60.
    access_token: Optional[str] = None

    # bot runtime configs
    superusers: Set[int] = set()
    nickname: Union[str, Set[str]] = ""
    command_start: Set[str] = {"/"}
    command_sep: Set[str] = {"."}
    session_expire_timeout: timedelta = timedelta(minutes=2)

    # custom configs
    # custom configs can be assigned during nonebot.init
    # or from env file using json loads

    class Config:
        extra = "allow"
        env_file = ".env.prod"