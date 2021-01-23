#! /bin/bash
#1.delete http/https and ,
cat privateURL.txt | sed 's/(http|https):\/\///g' | sed 's/\/\*//g' | sed "s/,/\r/g" > modify.txt
#2.sort all the domain and create folders
#cat modify.txt | sed 's/*//g' | awk -F '.' '{print $(NF-1)}' | sort -u | while read line;do if [ ! -d $line ];then mkdir $line;fi;done
#3.send *.domain to oneforall
cat modify.txt | grep '*\.' | sed "s/\///g" > prepareforenmusubdomains.txt
cat prepareforenmusubdomains.txt | while read line;do ping  $line;done
