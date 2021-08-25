# 工作坊网页-2021

---

### Members

[@alcedoM](https://github.com/alcedoM)

[@schrodingho](https://github.com/schrodingho)

[@tusihan](https://github.com/tusihan)

[@palpitate26](https://github.com/palpitate26)



## Install

克隆
```bash
$ git clone https://github.com/alcedoM/WIE-web.git
$ cd main/WIE
```
安装虚拟环境(已安装请忽略)

```bash
$ pip install pipenv
# 可以通过 pipenv --version 检查是否安装
```

安装依赖

```bash
$ pipenv install --dev
```
有个报错是pillow包安装问题，请手动安装

```bash
$ pipenv install pillow
```

生成虚拟数据(第一次启动时需要)

``` bash
$ pipenv shell # 进入虚拟环境
$ flask forge  # 生成虚拟数据
```

运行

```bash
$ flask run
* Running on http://127.0.0.1:5000/
```

测试用管理员

账号：admin@helloflask.com  密码：helloflask



## Update Log

- 8.25 
  - 前端：全部翻译，分数模块，禁止普通用户发帖
  - 后端：user数据库添加分数 

