#!/bin/bash
python src/robot/rebot.py $1 >/dev/null &
#/usr/lib/jvm/java-6-sun/jre/bin/java -Xmx1024m -Xss1024k -classpath /home/jth/opt/jython2.5.1/jython.jar: -Dpython.home=/home/jth/opt/jython2.5.1 -Dpython.executable=/home/jth/opt/jython2.5.1/jython org.python.util.jython src/robot/rebot.py $1 >/dev/null &
rebotpid=$!
while ps -ef | grep -v grep| grep $rebotpid > /dev/null; do
	top -b -p $rebotpid -n 1 | awk "/$rebotpid/ {print \$5,\$6,\$11}"
	sleep 1
done

exit 0
