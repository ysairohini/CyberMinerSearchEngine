两个 data 文件内容是一样的
分了 3 列方便插入数据库
title\link\description

数据源：google
搜索关键词来源：https://www.mondovo.com/keywords/most-searched-words-on-google/
List Of 1000 Most Searched Words On Google

# mysql set up

create database cyberminer;
use cyberminer;
drop table tbl_test;
CREATE TABLE tbl_test( id INT AUTO_INCREMENT PRIMARY KEY, title text , description text,url text);
