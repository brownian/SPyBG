#!/bin/bash
#
#


function cgiheader () {
	echo -e "Content-type: text/html\n\n"
}

function topheader () {
	echo '<H1>SPyBG Configuration</H1>'
}

function configs () {
	echo '<H2>Configuration files found:</H2>'

	[ -f $currconfig ] && currok="yes"
	[ -f $prevconfig ] && prevok="yes"
	[ -f $freshconfig ] && freshok="yes"


	echo '<UL>'

	if [ $currok = "yes" ] ; then
		cat <<CURROK
		<LI>Current configuration:
		    <A href="$urlpref/$currconfig" target="_blank">$currconfig</A>
CURROK
	fi

	if [ $prevok = "yes" ] ; then
		cat <<PREVOK
		<LI>Backup configuration:
		    <A href="$urlpref/$prevconfig" target="_blank">$prevconfig</A>
PREVOK
	fi

	if [ $freshok = "yes" ] ; then
		cat <<FRESHOK
		<LI>Fresh configuration:
		    <A href="$urlpref/$freshconfig" target="_blank">$freshconfig</A>
FRESHOK
	fi

	echo '</UL>'

}

function menu () {
	cat << MENU
	<H2>Safe actions:</H2>

	<OL>
	<LI><A href="`myURL`?action=prev2curr" target="_blank">view prev ini to current ini diff</A>
	<LI><A href="`myURL`?action=curr2fresh" target="_blank">view current ini to fresh ini diff</A>
	</OL>

	<H2>Real jobs:</H2>
	<UL>
	    <LI><SPAN style="font-weight: bold; color: blue;">Configuration INI files</SPAN>:
	      <OL>
		<LI><A href="`myURL`?action=copycurr2prev" target="_blank">backup current</A>&nbsp;&mdash;
			backup current global ini file
			(list of devices, fetched from SNMPc's mysql database)
			to "previous" (<TT><B>"$currconfig"</B></TT> to
			<TT><B>"$prevconfig"</B></TT>)
		<LI><A href="`myURL`?action=getfresh" target="_blank">get fresh</A>&nbsp;&mdash;
		    	get new "fresh" global ini file from mysql database;
			will be saved as <TT><B>"$freshconfig"</B></TT>
		<LI><A href="`myURL`?action=copyfresh2curr" target="_blank">use fresh</A>&nbsp;&mdash;
		    	copy fresh ini file to current working (<TT><B>"$freshconfig"</B></TT> to
			<TT><B>"$currconfig"</B></TT>)
		<LI>make list of new devices ("difference" between fresh and current)
		<LI><A href="`myURL`?action=viewlist"
			target="_blank">view</A>/<A href="`myURL`?action=editlist"
			target="_blank">edit</A> list of devices to update INI and RRD (see below)
		<LI><A href="`myURL`?action=listall"
			target="_blank">list all</A>&nbsp;&mdash; list all device names (in global INI file)
	      </OL>
	<BR>
	    <LI><SPAN class="warn">Devices' INI files and RRD bases:</SPAN>
	      <OL>
		<LI><A href="`myURL`?action=processlist"
			target="_blank" class="warn">proccess list</A>&nbsp;&mdash;
			update INI and RRD for devices specified in list (see above)
		<LI><A href="`myURL`?action=updateall"
			target="_blank" class="warn">update all
			ini and rrd files</A> using current ini file (update <B>ALL</B>)
	      </OL>
	</UL>
MENU

}

function echoSet () {
	HR
	set | sed -e 's/$/<BR>/'
}

function PREon () {
	echo "<PRE>"
}

function PREoff () {
	echo "</PRE>"
}

function myURL () {
	echo $REQUEST_URI | sed -e's/\?.*$//'
}

function goBack () {
	echo "Go <A href=\"`myURL`\">back</A>."
}

function closeLink () {
	echo "<A href=\"javascript:self.close()\">Close me</A>"
}

function HR () {
	echo "<HR>"
}

function BR () {
	echo "<BR>"
}

function notImplemented () {
	echo "Not implemented yet,"
	BR
	closeLink
	exit
}

function diffINI () {
	closeLink
	HR
	PREon
	diff -uN $1 $2
	PREoff
	HR
	closeLink
}

function getFresh () {
	closeLink
	BR
	echo "Some debug, dont worry:"
	PREon
	./getINIfromSNMPc.py 2>&1
	PREoff
	closeLink
}

function copyfresh2curr () {
	cp -f $freshconfig $currconfig \
		|| echo "Error occured.<BR>`closeLink`" \
		&& echo "Success.<BR>`closeLink`"
}

function copycurr2prev () {
	cp -f $currconfig $prevconfig \
		|| echo "Error occured.<BR>`closeLink`" \
		&& echo "Success.<BR>`closeLink`"
}

function updateall () {
	closeLink
	echo "<BR><SPAN style=\"color:red;\">Please wait, long action...</SPAN>"
	PREon
	./updateFiles.py -a --device ALL 2>&1
	PREoff
	closeLink
}

function viewlist () {
	closeLink
	PREon
	[ -f $1 ] \
		|| echo "No such file: $1." \
		&& cat $1
	PREoff
	closeLink
}

function editlist () {
	[ -f $1 ] \
		|| devices='' \
		&& devices=`cat $1`
	if [ "$submit" = "submit" ]; then
		#PREon
		#echo $formdevices | ./urldecode.sh
		#PREoff
		echo $formdevices | ./urldecode.sh | sed -e '/[A-Za-z]/ !d'> $1
		viewlist $1
	else
		closeLink
		cat << FORM
<FORM>
<TEXTAREA name="formdevices" cols="20" rows="30">
$devices
</TEXTAREA>
<BR>
<INPUT type="submit" name="submit" value="submit">
<INPUT type="reset">
<INPUT type="hidden" name="action" value="editlist">
<INPUT type="hidden" name="dodebug" value="$dodebug">
</FORM>
FORM
		closeLink
	fi
}

function processlist () {
	closeLink
	echo "<BR><SPAN style=\"color:red;\">Please wait, long action...</SPAN>"
	PREon
	./updateFiles.list.py -a --list $1 2>&1
	PREoff
	closeLink
}

function listall () {
	closeLink
	#echo "<HR><OL>"
	PREon
	cat alldevs.txt \
		| sed -e '
				#s/^/<LI>/g
				#s/ /<LI>/g
				s/^/\n/g
				s/ /\n/g
			'
	#echo "</OL><HR>"
	PREoff
	echo `wc -w alldevs.txt`'<BR>'
	closeLink
}

function doDebug () {
	[ "$dodebug" = "yes" ] && echoSet
}

#
#
#

workdir="/var/SPyBG"
cgidir="/usr/lib/cgi-bin"

urlpref="/spybg"

currconfig="hosts.ini"
prevconfig="hosts.ini.prev"
freshconfig="hosts.ini.fresh"
devicelist="devicelist.txt"

cgiheader

cat $cgidir/`basename $0`.head

cd $workdir || (
	echo "<H1 style=\"color:red;\">Can not chdir to $workdir</H1>"
	exit 255 )



# eval $QUERY_STRING
eval `echo $QUERY_STRING | tr '&' '; '`


if [ "$action" = "curr2fresh" ] ; then
	diffINI $currconfig $freshconfig

elif [ "$action" = "prev2curr" ] ; then
	diffINI $prevconfig $currconfig

elif [ "$action" = "getfresh" ] ; then
	getFresh

elif [ "$action" = "copycurr2prev" ] ; then
	copycurr2prev

elif [ "$action" = "copyfresh2curr" ] ; then
	copyfresh2curr

elif [ "$action" = "updateall" ] ; then
	updateall

elif [ "$action" = "viewlist" ] ; then
	viewlist $devicelist

elif [ "$action" = "editlist" ] ; then
	editlist $devicelist

elif [ "$action" = "listall" ] ; then
	listall

elif [ "$action" = "processlist" ] ; then
	processlist $devicelist

elif [ $action ] ; then
	notImplemented

else
	topheader
	configs
	menu
fi

doDebug
