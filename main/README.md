# 工作坊网站

## 安装

克隆
```bash
$ git clone https://github.com/alcedoM/WIE-web.git
$ cd main/WIE
```
创建虚拟环境

```bash
$ pip install pipenv
```

安装依赖

```bash
$ pipenv install --dev
```
有个报错是pillow包安装问题，请手动安装

```bash
$ pipenv install pillow
```

生成虚拟数据并运行

```bash
$ pipenv shell
$ flask forge
$ flask run
* Running on http://127.0.0.1:5000/
```
