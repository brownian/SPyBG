SPyBG Home
==========


Short description
-----------------
SPyBG is "SNMP Bulk Grapher, written in Python". It can get values, store in
rrd bases and graph them nicely.


Why
---

MRTG was too slow... Zabbix is excellent but it grabs values one by one, too,
and it appeared (for me) quite difficult to fetch a table of values and show
all those values as a bunch if graphs with interfaces' descriptions (from
another table).

So, that's why. SPyBG was written for this specific task -- to bulkwalk whole
tables (ifInOctets or ifHCInOctets, let's say -- for/with all indexes, and
ifDescr or ifAlias for all those interfaces), creates rrd bases for every index
on-the-fly, stores that values and produces html pages with graphs (by means of
cgi scripts).


Status
------

On the way forward .)

Some things need to be rewritten, some features i'd love to add.


License
-------
GPLv3 or like that.

