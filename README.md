# 工作坊网页-2021

---

### Members

[@alcedoM](https://github.com/alcedoM) [@schrodingho](https://github.com/schrodingho)[@tusihan](https://github.com/tusihan)[@palpitate26](https://github.com/palpitate26)



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

测试用管理员

账号：admin@wie.com  密码：helloadmin

