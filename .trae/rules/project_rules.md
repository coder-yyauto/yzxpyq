特别设定：本环境是开发/生产合一的环境，所有的代码都在同一个环境中运行。
阿里云的alinux3环境, 内存8G, 4核CPU, 工作在yzxuser用户下。
使用micromamba管理python环境。yzxuser用户下默认安装了yzx环境并设定自动激活。
只有在yzx环境下才能运行代码。
只有在yzx环境下才能使用micromamba安装python包。
如果conda-forge渠道没有提供某个包，可以使用yzx环境下的pip安装。
