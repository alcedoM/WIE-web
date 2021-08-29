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
  - 后端：
    - user数据库添加分数
    - 管理员分数修改
  
- 8.26
  - 前端: 
    - 增加排行榜页面
    - 细节修改
    - 注册需要学号，管理员面板查看学号
    - 发文章模块（待完善）
    - 文章后台管理（部分）
  - 后端：
    - 排行榜后端
    - 发文章后端（待完善）
    - 文章管理后端
- 8.29
  - 文章发布界面富文本编辑器（需要安装flask-ckeditor）

    ```bash
    $ pipenv install flask-ckeditor
    ```

  - 展示文章
  - 权限更改

