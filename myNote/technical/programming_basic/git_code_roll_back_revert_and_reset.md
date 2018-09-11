---
title: "git 代码回滚与爬坑 -- reset and revert"
date: 2018-09-11T10:30:00+08:00
toc: true

categories:
- "programming basic"

tags:
- "git"

---

# reset

某些特殊的情况下，需要回退到先前的某一次提交。

git log 查找想要回退的commit的id后运行：

`git reset --hard 2c1e288`

回退后git log只会显示回退版本之前的提交。如果需要返回最新的提交，使用git reflog查看对应的id。

**git reset只适合本地的回退和查看先前代码。如果远程仓库已有最新的提交，git会认为远程仓库的代码较新，需要先同步远程代码再进行修改，此情况下建议使用revert。**


# git reset --soft --mixed --hard

以`HEAD～`为例（HEAD前的一次提交）

`git reset --soft HEAD~`  会回到前一次提交的commit执行之前的状态
`git reset --mixed HEAD~`  会回到前一次提交的add执行之前的状态
`git reset --hard HEAD~`  会回到前一次提交的add执行之前的状态，并且将目录里的所有文件调整为前一次的提交状态

通常回退时需要将文件也回退需要加 --hard 标签。

# git的文件组织

git将所有的文件以hash码命名放在仓库中存储。

HEAD指针，一般可以理解为当前commit状态的一个快照（指向仓库中当前commit的所有的文件）。每次commit或者merge等会创建新的commit节点时，会让HEAD指向新的位置。

reset会改变HEAD指针的位置与HEAD对应的分支指针的位置，checkout只会改变HEAD指针指向的分支。

# revert

`git revert <commit-id>` **相当于取消一次commit ，会让结果和没有<commit-id>这一次提交一样，并非像reset那样直接回到某一次commit的代码。**

使用revert不会破坏历史记录，只是提交一个新的修改使修改后代码和以前一致。

实质上相当于用<commit-id>前的代码merge <commit-id>后的代码，因此如果后面对代码文件做了修改需要解决冲突。

# revert一个merge commit

**注意revert用在merge的commit上的情况有坑**

`git revert <commit-id> -m 1 ` 需要添加-m参数，指定是merge前的第几个分支（git log上的merge后）。

revert的主要麻烦：如果存在分支合并的情况，如下，从m1 revert到a2时会添加一个新的提交m2，**当m2与b2 merge时会显示已经merge过**。

a1 -> a2 -> m1 -> m2
  b1 -> b2 /

**因此在两个分支还需要合并时，不能直接使用merge，而要先revert上一次的revert，让两次revert抵消，也就是 ` git revert <m2 commit id>` 。**

为了少折腾，碰到两个分支以后注定还是要合并的情况，还是不要revert了吧，或者revert之后改完相应的代码就revert回来，貌似没人提到更好的解决方案....

# 不常用的回退

以下命令存在危险性不建议使用，而且一般也没有使用必要。注意某些操作针对未提交前的处理，可能导致对文件修改的丢失。git对已提交的文件几乎总是可以恢复的，因此建议尽量在提交后处理。

` git checkout <file>` 撤销文件修改（到上一次提交）。
` git commit --amend` 重新提交，提交后删除上一次提交。 

