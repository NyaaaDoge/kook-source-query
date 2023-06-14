# Kook-Source-Query Bot

Kook Steam 起源/金源 游戏服务查询Bot，支持频道设置批量查询。  

## 功能

支持CS:GO、CS:S、CS、GMOD、L4D2等游戏服务器查询。一个服务器最多设置30个（默认数量）查询；一个频道最多设置15个（默认数量）查询，可以分频道设置对应批量查询。可以自行部署。  

命令列表:  

| 指令（需要在频道输入）                 | 功能                                   | 备注                                              |
|-----------------------------|--------------------------------------|-------------------------------------------------|
| `/help`                     | 查询帮助指令                               | /                                               |
| `/query ip [ip:端口]`         | 查询对应IP的服务器信息                         | 举例:`/query ip 216.52.148.47:27015`              |
| `/query server`             | 查询该频道设置好的IP地址列表的服务器信息                | 需要使用`/config query [ip:端口]`先配置设置                |
| `/query sub [map_name]`     | 订阅特定地图，Bot监测到设定好的服务器有特定地图将会私信通知。     | 需要Bot管理员手动用`/admin track [ip:port]`设定监测服务器列表    |
| `/query unsub [map_name]`   | 取消订阅特定地图。                            | /                                               |
| `/config query [ip地址:端口号]`  | 配置当前频道查询的IP地址                        | /                                               |
| `/config delete [ip地址:端口号]` | 删除设置里面当前频道对应的IP地址                    | /                                               |
| `/config showip [on/off]`   | 为当前频道的查询设置显示/关闭IP地址结果                | /                                               |
| `/config showimg [on/off]`  | 为当前频道的查询设置显示/关闭预览图片，关闭图片后可以有效提高查询速度。 | /                                               |
| `/config`                   | 查看当前频道查询的设置信息和当前服务器的设置信息             | /                                               |
| `/hellosrc`                 | 查看Bot是否还活着                           | /                                               |
| @机器人+关键词"查"                 | 快捷查询对应IP的服务器信息                       | 只要在频道发送消息里面有关键字“查”并且@机器人即可查询。功能同`/query server` |

Bot设置了查询`60s`缓存，防止重复查询。  

Bot管理员命令：

| 指令（需要在频道输入）                | 功能               | 备注                               |
|----------------------------|------------------|----------------------------------|
| `/admin update maplist`    | 更新地图图片JSON数据     | /                                |
| `/admin update track`      | 手动执行服务器监测任务      | /                                |
| `/admin insert [ip:port]`  | 直接在当前频道插入配置的查询地址 | /                                |
| `/admin leave [gid]`       | 离开特定Guild的服务器    | 需要进行二次确认                         |
| `/admin track [ip:port]`   | 为Bot添加服务器监控列表    | `/admin track`可以查看当前Bot服务器监控配置信息 |
| `/admin untrack [ip:port]` | 删除服务器监控列表中的特定地址  | /                                |

Bot使用轮询的方式监测服务器信息，如果符合用户订阅地图名则向用户推送通知。

## 如何使用？

### 1. 部署与初始化

为自己对应的系统安装 `Python` 并且版本等于或高于 `3.10`，打开终端窗口输入以下命令：  
~~~
pip install -r requirements.txt
~~~
在`bot/bot_configs`里面填写对应的Token和开发者ID，然后 python3 main.py运行即可。  
首次使用需要先更新地图图片JSON数据，可以在运行之后在任一频道使用`/admin update maplist`来更新地图图片JSON数据。  

### 2. 使用

在需要查询的频道直接使用命令如`/query ip 216.52.148.47:27015`可以直接查询到服务器信息，如果有图片则显示大图。主要显示CSGO地图的预览图。  
需要配置频道默认的查询使用命令如`/config query 216.52.148.47:27015`可以添加到默认查询地址里面。配置完后直接使用`/query server`即可查询到服务器信息。  
如果需要显示/关闭IP地址请使用`/config showip [on/off]`。开启关闭预览图片使用`/config showimg [on/off]`。  

## 依赖

* [python-a2s](https://github.com/Yepoleb/python-a2s) - 用于查询起源/金源服务器的库  
* [khl.py](https://github.com/TWT233/khl.py) - Kook社区python机器人框架  
* [csgo-map-images](https://github.com/NewPage-Community/csgo-map-images) - 机器人地图图片  

觉得不错的话在 Github 点个 star 吧！  
或者在 [爱发电](https://afdian.net/a/NyaaaDoge) 支持开发者。  
