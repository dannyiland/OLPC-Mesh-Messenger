# Copyright (C) 2012, Danny Iland <iland@cs.ucsb.edu>
# Copyright (C) 2012, Don Voita <don@cs.ucsb.edu>
# Copyright (C) 2009, Benjamin M. Schwartz <bmschwar@fas.harvard.edu>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

import logging
import telepathy
import gtk
import hashlib
import pango
import dobject.groupthink as groupthink
import dobject.groupthink.gtk_tools as gtk_tools
import dobject.groupthink.sugar_tools as sugar_tools
import sugar
import pygtk 
import gobject
import hashlib
import time
import subprocess
pygtk.require("2.0")
from sugar.activity import activity
from datetime import datetime
from sugar.datastore import datastore
import cPickle
import os, os.path
from multiprocessing import Process, Lock
import json
import urllib2
import random
import string
import pickle
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
from geopy import geocoders  
from sugar.presence import presenceservice

logger = logging.getLogger('disaster')

# IP to Ping
IP_ADDR = "4.2.2.3"  
# Time between checks in Milliseconds
TIMER = 15000  
OUR_ACTIVITY_NAME = "Disaster Activity"
# sharing scopes from sugar activity
SCOPE_PRIVATE = "private"
SCOPE_INVITE_ONLY = "invite"  # shouldn't be shown in UI, it's implicit
SCOPE_NEIGHBORHOOD = "public"
DEBUG = True
MESSAGES_CREATED = 1000

def messageCodec(score_or_opaque, pack_or_unpack):
    message = score_or_opaque
    if pack_or_unpack:
        return (message.title, message.message, message.location, message.time, message.category)
    else:
        return ImmutableMessage(title=message[0],
                              message=message[1],
                              location=message[2],
                              time=message[3],
                              category=message[4],)

class ImmutableMessage(object):
    def __init__(self, title="", message="", location="", time="", category=""):
        hashing = hashlib.sha256()
        hashing.update(title)
        hashing.update(message)
        hashing.update(location)
        self.hashed = hashing.hexdigest()
        self.title = title
        self.message = message
        self.location = location
        self.time = time
        self.category = category
         
class DisasterActivity(groupthink.sugar_tools.GroupActivity):
    
    def runTests(self,combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            name = model[tree_iter][0]
            # logger.debug(name)
            if name == 'Create 1000 messages':
                for n in xrange(1000):
                    title = "message " + str(n)
                    message = "".join( [random.choice(string.letters) for i in xrange(512)] )
                    location = "".join( [random.choice(string.letters) for i in xrange(32)] )
                    category = random.choice([1,2,3,4,5])
                    self.displayMessage(self.createEntry(title, message, location, category))
                    
            elif name == 'Create 500 messages':
                for n in xrange(500):
                    title = "message " + str(n)
                    message = "".join( [random.choice(string.letters) for i in xrange(512)] )
                    location = "".join( [random.choice(string.letters) for i in xrange(32)] )
                    category = random.choice([1,2,3,4,5])
                    self.displayMessage(self.createEntry(title, message, location, category))
            elif name == 'Create 100 messages':
                for n in xrange(100):
                    title = "message " + str(n)
                    message = "".join( [random.choice(string.letters) for i in xrange(512)] )
                    location = "".join( [random.choice(string.letters) for i in xrange(32)] )
                    category = random.choice([1,2,3,4,5])
                    self.displayMessage(self.createEntry(title, message, location, category))

            elif name == 'Create 1 message':
                title = "message"
                message = "".join( [random.choice(string.letters) for i in xrange(512)] )
                location = "".join( [random.choice(string.letters) for i in xrange(32)] )
                category = random.choice([1,2,3,4,5])
                self.displayMessage(self.createEntry(title, message, location, category))
            elif name == 'Remove file':
                try:
                    os.remove(os.path.join(self.get_activity_root(), 'data', 'messagesAndCures.cpkle'))
                except Exception as e:
                    logger.debug("Exception in runTests: " + repr(e))  

                #self.cloud.messages = groupthink.CausalDict(value_translator=messageCodec)
                #self.cloud.cures = groupthink.CausalDict()
                #for message in self.cloud.messages:
                #    self.displayMessage(message)
            

    # Get lat/long from descriptive name, using Google Maps Geocoder. Return (False,False) if unknown.
    def getLocationByName(self, locationName):
        try:
            g = geocoders.Google()
            place, (lat, lng) = g.geocode(locationName)
            return (lat, lng)
        except Exception, e:
            logger.debug("geocode failed: " + str(e))
            return (False, False)

    # Looping timer, calls internetCheck every 15 seconds.
    def fifteenSecondTimer(self):
        gobject.timeout_add(TIMER, self.internetCheck_cb)
    
    # One second callback used for timer
    def oneSecondTimer(self):
        gobject.timeout_add(1000, self.updateTime_cb)

     # Every second, decriment the timer
    def updateTime_cb(self):
        self.time_count = self.time_count - 1
        if self.time_count < 1:
            self.time_count = TIMER/1000
        if DEBUG:
            self.timerButton.set_text("Polling in " + str(self.time_count) + " seconds.")
        return True

    # Check for internet access. 
    def hasInternet(self):
        # returns True if internet, else False
        ret = subprocess.call("ping -w 1 -c 1 %s" % IP_ADDR, shell=True,stdout=open('/dev/null', 'w'), stderr=subprocess.STDOUT)
        if ret == 0:
            logger.debug("Internet access found.")
            self.HTTPgetCures()
            return True
        else:
            logger.debug("No Internet access ;(")
            return False
    
 
    # Upload all un-uploaded messages to Ushahidi. 
    # Create cure for each message successfully uploaded.

    # Example POST:
    # http://<somedomain>/api?task=report&incident_title=Test&incident_description=Testing+with+the+api &incident_date=03/18/2009&incident_hour=10&incident_minute=10&incident_ampm=pm &incident_category=2,4,5,7&latitude=-1.28730007&longitude=36.82145118200820&location_name=accra &person_first=Henry+Addo&person_last=Addo&person_email=henry@ushahidi.com&resp=xml
        
    # Efficieny todo: keep data strcture of unuploaded messages
    def HTTPuploadMessages(self):
        uploaded = False
        for h, message in self.cloud.messages.items():
            if h not in self.cloud.cures.keys():
                try:
                    # Some dirty things to get strings submittable to Ushahidi.
                    if len(message.message) < 3:
                        message.message = message.message + "   " 
                    if len(message.title) < 3:
                        message.title = message.title + "   " 
                    # Get message date/time, convert to required format for POST
                    t = time.strptime(message.time, "%Y-%m-%d %H:%M:%S")
                    #  mm/dd/yyyy.
                    month = str(t.tm_mon)
                    if(t.tm_mon) < 10:
                        month = "0" + month
                    day = str(t.tm_mday)
                    if(t.tm_mday) < 10:
                        day = "0" + day
                    incidentDate = "/".join([month,day,str(t.tm_year)])
                    #logger.debug("Uploading with date: " + incidentDate)
                    if t.tm_hour < 12:
                        ampm = "am"
                    else:
                        ampm = "pm"
                    minute = str(t.tm_min)
                    if t.tm_min < 10:
                        minute = "0" + minute
                    hour = str(t.tm_hour % 12)
                    if (t.tm_hour % 12) < 10:
                        hour = "0" + hour
                    (lat, lng) = self.getLocationByName(message.location)
                    if lat is False or lng is False:
                        latitude = "34.41421"
                        longitude="-119.840798"
                    else:
                        latitude = lat
                        longitude = lng
                    register_openers()
                    datagen, headers = multipart_encode({"task":"report", "incident_title":message.title, "incident_description":message.message,"incident_date":incidentDate,"incident_hour":hour,"incident_minute":minute,"incident_ampm":ampm,"incident_category":message.category,"latitude":latitude,"longitude":longitude,"location_name":message.location,"hash":message.hashed})
                    request = urllib2.Request("http://128.111.41.47/ushahidi/api", datagen, headers)
                    f = urllib2.urlopen(request)
                    response = f.read()
                    # Parse JSON response, look for
                    # "error":{"code":"0","message":"No Error"}}
                    #logger.debug("received response: " + response)
                    response_object = json.loads(response)
                    if response_object["error"]["code"] == "0":
                        #logger.debug("Successfully uploaded message with hash " + h + " , added to CureList")
                        self.cloud.cures[h] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                        #logger.debug("Added cure " + h )
                        uploaded = True
                    f.close()
                except Exception as e:
                    logger.debug(e)  

        if uploaded:
            self.addToFile(self.lock)
            self.HTTPshowCures(self.cloud.cures)

    def HTTPgetMessages(self):
        return True

    def HTTPgetCures(self):
        request = urllib2.Request("http://128.111.41.47/ushahidi/api?task=cure&action=get")
        f = urllib2.urlopen(request)
        response = f.read()
        #logger.debug(response)
        response_object = json.loads(response)
        # LIST OF DICTS
        cures = response_object["payload"]["cures"]
        for cure in cures:
            theHash = ""
            theDate = ""
            for key,value in cure.items():
                if key is "created":
                    theDate = value
                if key is "hash":
                    theHash = value
            if theHash not in self.cloud.cures.keys():
                self.cloud.cures[theHash]=theDate
        f.close()
        self.HTTPshowCures(self.cloud.cures)
        return True

    def HTTPshowCures(self, cureDict):
        for hashes, entry in self.entryDict.items():
            if hashes in cureDict.keys():
                self.tableModel.set_value(entry, 5, "Yes - " + cureDict[hashes])

    # Writes all current messages and cures to a file
    def addToFile(self, lock):
        lock.acquire()
        #logger.debug("Lock aquired, saving to data/messagesAndCures.cpkle")
        try:
            f = open(os.path.join(self.get_activity_root(), 'data', 'messagesAndCures.cpkle'), 'wb')
            f.write(self.cloud.dumps())
            f.close()
        except Exception as e:
            logger.debug("Error writing to file" + repr(e))  
        lock.release()
        return True
    
    #Called when entries are added to the CausalDict by neighbors
    def neighborAdded_cb(self, dict_added, dict_removed):
        logger.debug("Receiving " + str(len(dict_added)) + " messages.")
        if DEBUG:
            self.dict_size = self.dict_size + len(dict_added)
            if self.dict_size >= MESSAGES_CREATED:
                logger.debug("Dict size is now " + str(self.dict_size))
        self.addToFile(self.lock)
        for k,v in dict_added.items():
            self.displayMessage(v)

    #Called when entries are added to the cures list by neighbors
    def newCures_cb(self, dict_added, dict_removed):
        logger.debug("Receiving " + str(len(dict_added)) + " cures.")
        if DEBUG:
            self.cure_size = self.cure_size + len(dict_added)
            if self.cure_size >= MESSAGES_CREATED:
                logger.debug("Cure size is now " + str(self.cure_size))
        self.addToFile(self.lock)
        self.HTTPshowCures(dict_added)

    # Called every 15 seconds
    def internetCheck_cb(self):
        self.time_count = 15      
#        self.autoJoin()
        if self.hasInternet():
            self.HTTPuploadMessages()
            self.HTTPgetMessages()
            self.HTTPgetCures()
        return True

    def displayMessage(self, message, myFilter=None):
#        for key,value in self.cloud.messages.items():
        newEntry = self.tableModel.insert_before(None, None)
        self.tableModel.set_value(newEntry, 0, message.title)
        self.tableModel.set_value(newEntry, 1, message.message)
        self.tableModel.set_value(newEntry, 2, message.location)
        self.tableModel.set_value(newEntry, 3, message.time)
        self.tableModel.set_value(newEntry, 4, self.categories[message.category])
        if message.hashed in self.cloud.cures.keys():
            self.tableModel.set_value(newEntry, 5, "Yes")
        else:
            self.tableModel.set_value(newEntry, 5, "Unknown")
        self.treeView.expand_all()   
        self.entryDict[message.hashed] = newEntry

    # Example creation with auto-detected time
    def createEntry(self, title="", message="", location="", category=""):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        newMessage = ImmutableMessage(title, message, location, now, category)
        self.cloud.messages[newMessage.hashed] = newMessage
        self.addToFile(self.lock)
        return newMessage
     

    # double click on entry in table.
    def messageSelected(self, widget, row, column):
        model = widget.get_model()
        dialog = gtk.Dialog("Message Details",
                            None,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
        title = gtk.Label("Title:  ")
        titleText = model[row][0]
        titleTextLabel = gtk.Label(titleText)
        titleBox = gtk.HBox()
        titleBox.pack_start(title)
        titleBox.pack_start(titleTextLabel)        
        
        message = gtk.Label("Message:  ")
        messageText = model[row][1]
        messageTextLabel = gtk.Label(messageText)
        messageBox = gtk.HBox()
        messageBox.pack_start(message)
        messageBox.pack_start(messageTextLabel)

        location = gtk.Label("Location:  ")
        locationText = model[row][2]
        locationTextLabel = gtk.Label(locationText)
        locationBox = gtk.HBox()
        locationBox.pack_start(location)
        locationBox.pack_start(locationTextLabel)

        time = gtk.Label("Time:     ")
        timeText = model[row][3]
        timeTextLabel = gtk.Label(timeText)
        timeBox = gtk.HBox()
        timeBox.pack_start(time)
        timeBox.pack_start(timeTextLabel)

        categoryLabel = gtk.Label("Category: ")
        sharedText = model[row][4]
        sharedTextLabel = gtk.Label(sharedText)
        sharedBox = gtk.HBox()
        sharedBox.pack_start(categoryLabel)
        sharedBox.pack_start(sharedTextLabel)

        dialog.vbox.pack_start(titleBox)
        dialog.vbox.pack_start(messageBox)
        dialog.vbox.pack_start(locationBox)
        dialog.vbox.pack_start(timeBox)
        dialog.vbox.pack_start(sharedBox)
        
        dialog.show_all()
        titleBox.show()
        response = dialog.run()
        dialog.destroy()
        
        
    def clicked(self, widget, title, message, location):
        # Add entry to CausalDict from topBox data
        newEntry = self.createEntry(
            title.get_text(), 
            message.get_buffer().get_text(message.get_buffer().get_start_iter(), message.get_buffer().get_end_iter(), True),
            location.get_text(),
            self.categoryPicker.get_active()+1

            )
        title.set_text("")
        message.get_buffer().delete(message.get_buffer().get_start_iter(), message.get_buffer().get_end_iter())
        location.set_text("")
        self.displayMessage(newEntry)

    def early_setup(self):
        self.entryDict = dict()
        self.time_count = TIMER/1000
        self.fifteenSecondTimer() #Look for network to join
        self.oneSecondTimer() #Decriment second counter
        
        self.categories = dict()
        self.categories[1]="Emergency"
        self.categories[3]="Hazard"
        self.categories[5]="Help and Support"
        self.categories[2]="Security Threat"
        self.categories[4]="Trusted Report"
        self.dict_size = 0
        self.cure_size = 0

    def clear(self, widget, title, message, location):
        title.set_text("")
        message.get_buffer().delete(message.get_buffer().get_start_iter(), message.get_buffer().get_end_iter())
        location.set_text("")

    def close(self, skip_save=False):
        activity.Activity.close(self,  True)

    def __init__(self, handle, create_jobject=True):
        super(DisasterActivity, self).__init__(handle)

    def initialize_display(self):
        self.layout = gtk.Table(9, 1)
        self.lock = Lock()
        self.cloud.messages = groupthink.CausalDict(value_translator=messageCodec)
        self.cloud.cures = groupthink.CausalDict()
        # Load messages if they exist
        try:
            f = open(os.path.join(self.get_activity_root(), 'data', 'messagesAndCures.cpkle'), 'r')
            self.cloud.loads(f.read())
            f.close()
        except Exception, e:
            logger.debug('First run, no messages.')

        self.topBox = gtk.VBox()
        # Toolbar
        toolBar = gtk.Toolbar()
        toolTips = gtk.Tooltips()
        toolBar.set_style(gtk.TOOLBAR_TEXT)

        # Toolbar Buttons
        if DEBUG:
            self.timerButton = gtk.Label("Polling in 15 seconds!")
        self.myMessagesButton = gtk.ToolButton(None, "My Messages")
        self.myMessagesButton.set_expand(False)
        self.myMessagesButton.set_tooltip(toolTips, 'View Messages you have sent')
        self.myMessagesButton.connect("clicked", self.myMessages)
    
        self.allMessagesButton = gtk.ToolButton(None, "All Messages")
        self.allMessagesButton.set_expand(False)
        self.allMessagesButton.set_tooltip(toolTips, 'View all messages')
        self.allMessagesButton.connect("clicked", self.allMessages)

        self.settingsButton = gtk.ToolButton(None, "Settings")
        self.settingsButton.set_expand(False)
        self.settingsButton.set_tooltip(toolTips, 'Me too')
        self.settingsButton.connect("clicked", self.settings)
       
        self.helpButton = gtk.ToolButton(None, "Help")
        self.helpButton.set_expand(False)
        self.helpButton.set_tooltip(toolTips, 'How to use this activity')
        self.helpButton.connect("clicked", self.help)
        toolBar.insert(self.myMessagesButton, 0)
        toolBar.insert(self.allMessagesButton, 1)
        toolBar.insert(self.settingsButton, 2)
        toolBar.insert(self.helpButton, 3)
        
        # Entry fields
        titleBox = gtk.HBox()
        messageBox = gtk.HBox()
        locationBox = gtk.HBox()
        categoryBox = gtk.HBox()
       
        # Labels
        titleLabel = gtk.Label("Title: ")
        messageLabel = gtk.Label("Message: ")
        locationLabel = gtk.Label("Location: ")
        categoryLabel = gtk.Label("Category: ")
        publicLabel = gtk.Label("Visibility: ")
        messageLabel.set_line_wrap(True)

        # Text entry box for title
        self.titleEntry = gtk.Entry(max=50)
        self.titleEntry.set_has_frame(False)        
        # Text entry box for message
        self.messageEntry = gtk.TextView()
        self.messageEntry.set_property("editable", True)

        # Text entry box for location
        self.locationEntry = gtk.Entry(max=50)
        self.locationEntry.set_has_frame(False)

        # Category selector
        self.categoryPicker = gtk.combo_box_new_text() 
        for k,cat in self.categories.items():
            self.categoryPicker.append_text(cat)
        # Privacy selector
        self.privacyPicker = gtk.combo_box_new_text()
        self.privacyPicker.append_text("Private")
        self.privacyPicker.append_text("Public")
        self.privacyPicker.set_active(1)

        # Create row for category and privacy
        categoryBox.pack_start(categoryLabel, expand=False)
        categoryBox.pack_start(self.categoryPicker)
        categoryBox.pack_start(publicLabel, expand=False)
        categoryBox.pack_start(self.privacyPicker)

        # TEST mode, includes timer and message creation/deletion
        if DEBUG:
            categoryBox.pack_start(self.timerButton)
            self.tests = list()
            self.tests.append("Create 1 message")
            self.tests.append("Create 100 messages")
            self.tests.append("Create 500 messages")
            self.tests.append("Create 1000 messages")
            self.tests.append("Remove file")
            testLabel = gtk.Label("Test:")
            self.testPicker = gtk.combo_box_new_text()
            self.testPicker.connect("changed", self.runTests)
            for test in self.tests:
                self.testPicker.append_text(test)
            categoryBox.pack_start(self.testPicker)
            
        # Packing all into top Box
        titleBox.pack_start(titleLabel, expand=False)
        titleBox.pack_start(self.titleEntry)
        messageBox.pack_start(messageLabel, expand=False)
        messageBox.pack_start(self.messageEntry)
        locationBox.pack_start(locationLabel, expand=False)
        locationBox.pack_start(self.locationEntry)
                
        # Place buttons on GUI
        buttonBox = gtk.HBox()
        submitButton = gtk.Button(label="Submit", stock=None)
        clearButton = gtk.Button(label="Clear", stock=None)
        submitButton.connect("clicked", self.clicked, self.titleEntry, self.messageEntry, self.locationEntry)
        clearButton.connect("clicked", self.clear, self.titleEntry, self.messageEntry, self.locationEntry)
        buttonBox.pack_start(submitButton)
        buttonBox.pack_start(clearButton)
        # Place top half on GUI
        self.topBox.pack_start(titleBox)
        self.topBox.pack_start(categoryBox)
        self.topBox.pack_start(messageBox, False, False, 0)
        self.topBox.pack_start(locationBox)
        self.topBox.pack_start(buttonBox)

        # Start bottom box
        self.bottomBox = gtk.VBox()
        messageTable = gtk.VBox()
        
        # Table object
        self.tableModel = gtk.TreeStore(gobject.TYPE_STRING,       # title
                                        gobject.TYPE_STRING,  # message
                                        gobject.TYPE_STRING,  # location
                                        gobject.TYPE_STRING,  # time
                                        gobject.TYPE_STRING,   # Category
                                        gobject.TYPE_STRING)  # Received
        
        self.treeView = gtk.TreeView(self.tableModel)
        self.treeView.connect("row-activated", self.messageSelected)
        self.treeView.set_rules_hint(True)
        self.scrolledTreeView = gtk.ScrolledWindow(hadjustment=None, vadjustment=None)
        self.scrolledTreeView.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        self.scrolledTreeView.add(self.treeView)
        

        cellRenderer = gtk.CellRendererText()
        col1 = gtk.TreeViewColumn("Title", cellRenderer, text=0)
        col2 = gtk.TreeViewColumn("Message", cellRenderer, text=1)
        col3 = gtk.TreeViewColumn("Location", cellRenderer, text=2)
        col4 = gtk.TreeViewColumn("Time", cellRenderer, text=3)
        col5 = gtk.TreeViewColumn("Category", cellRenderer, text=4)
        col6 = gtk.TreeViewColumn("Received?", cellRenderer, text=5)

        col1.set_resizable(True)
        col2.set_resizable(True)
        col3.set_resizable(True)
        col4.set_resizable(True)
        col5.set_resizable(True)
        col6.set_resizable(True)

        self.treeView.append_column(col1)
        self.treeView.append_column(col2)
        self.treeView.append_column(col3)
        self.treeView.append_column(col4)
        self.treeView.append_column(col5)
        self.treeView.append_column(col6)

        self.treeView.expand_all()
 
        messageTable.pack_start(self.scrolledTreeView)
        self.bottomBox.pack_start(messageTable)

        self.layout.attach(toolBar, 0, 1, 0, 1)
        self.layout.attach(self.topBox, 0, 1, 1, 4)
        self.layout.attach(self.bottomBox, 0, 1, 4, 9)

        self.cloud.messages.register_listener(self.neighborAdded_cb)
        self.cloud.cures.register_listener(self.newCures_cb)
        #self.share(private=False)
        return self.layout

    # Joins the activity given by activity_id
    def handleJoin(self, activity_id, share_scope=SCOPE_PRIVATE):
        self.mypservice = presenceservice.get_instance()
        mesh_instance = self.mypservice.get_activity(activity_id,warn_if_none=False)
        logging.debug("*** Act %s, mesh instance %r, scope %s",
                      activity_id, mesh_instance, share_scope)
        if mesh_instance is not None:
            # There's already an instance on the mesh, join it
            logging.debug("*** Act %s joining existing mesh instance %r",
                          activity_id, mesh_instance)
            self.shared_activity = mesh_instance
            self.shared_activity.connect('notify::private',
                                         self._Activity__privacy_changed_cb)
            self._join_id = self.shared_activity.connect("joined",
                                                         self._Activity__joined_cb)
            if not self.shared_activity.props.joined:
                logger.debug("Calling .join() in handleJoin")
                self.shared_activity.join()
            else:
                self._Activity__joined_cb(self.shared_activity, True, None)
        elif share_scope != SCOPE_PRIVATE:
            logging.debug("*** Act %s no existing mesh instance, but used to " \
                          "be shared, will share" % activity_id)
            # no existing mesh instance, but activity used to be shared, so
            # restart the share
            if share_scope == SCOPE_INVITE_ONLY:
                self.share(private=True)
            elif share_scope == SCOPE_NEIGHBORHOOD:
                self.share(private=False)
            else:
                logging.debug("Unknown share scope %r" % share_scope)

    def autoJoin(self):
        logger.debug("In autoJoin")
        buddyCount= dict()
        for activity in self.pservice.get_activities():
            if activity.get_properties("name")[0] == OUR_ACTIVITY_NAME:
                id = activity.get_properties("id")[0]
                buddyCount[id] = len(activity.get_joined_buddies())
                logger.debug("ID is : " + str(id) + " count is " + str(buddyCount[id]))
        maxValue = 0
        largestGroup = None
        for id, value in buddyCount.items():
            if value > maxValue:
                largestGroup = id
                maxValue = value
            elif value == maxValue:
                if id > largestGroup:
                    largestGroup = id
        # We know we are the only people if this is None
        if largestGroup != None:
            logger.debug("Largest group: " + largestGroup + " with size " + str(maxValue))
            if largestGroup != self.get_id():
                if self.shared_activity:
                    self.shared_activity.leave()
                    self.shared_activity._activity.Leave(reply_handler=self._leave_cb,
                             error_handler=self._leave_error_cb)
                self.handleJoin(largestGroup, SCOPE_PRIVATE)
        else:
            self.share(private=False)



    def _leave_cb(self):
        """Callback for async action of leaving shared activity."""
        self.shared_activity.emit("joined", False, "left activity")
        
    def _leave_error_cb(self, err):
        """Callback for error in async leaving of shared activity."""
        logger.debug('Failed to leave activity: %s', err)


# Find a shared activity to join. If none are found, share yourself. Triggered every 15 seconds.
#    def autoJoin(self):
#        logger.debug("In Autojoin")
#        self.update_timer_cb(TIMER/1000)

        # Poll for new neighbors
#        self.joined = False
#        activities = self.pservice.get_activities()
        

#        current_ids = []
#        if self.shared_activity:
#            self.joined = True
 #           buddies = self.shared_activity.get_joined_buddies()
 #           for buddy in buddies:
 #               acts = buddy.get_joined_activities()
 #               for pact in acts:
 #                   act_id = pact.get_properties("id")[0]
 #                   current_ids.append(act_id)
 #           logger.debug("Avoiding joining buddy activities: ")
 #           logger.debug("\n".join(current_ids))
        
        # Who is out there besides me?
 #       else: 
 #           my_id = self.get_id()
 #           for act in activities:
 #               act_id = act.get_properties("id")[0]
 #               act_name = act.get_properties("name")[0]
 #               logger.debug(act_id + " " + act_name)
 #               if act_name == OUR_ACTIVITY_NAME:
 #                   logger.debug("Found Disaster Activity")
                    # Skip myself
 #                   if act_id == my_id:
 #                       logger.debug("Found Disaster Activity with same ID")
 #                   elif act_id in current_ids:
                        # Don't try to join with if already joined i.e. buddies
 #                       logger.debug("Found a buddy.")
  #                      pass
   #                 else:
    #                    logger.debug("Found Disaster Activity with different ID")
     #                   if not self.joined:
      #                      logger.debug("calling handleJoin")
       #                     self.handleJoin(act_id, SCOPE_PRIVATE) 
        #                    self.joined = True
         #                   logger.debug("Joining shared activity automatically")
 #       if not self.joined:
  #          logger.debug("Calling self.share()")
   #         self.share(private=False)
        
    def settings(self, widget):
        logger.debug('clicked settings.')
        self.layout.attach(self.topBox, 0, 1, 1, 4)
        self.layout.attach(self.bottomBox, 0, 1, 4, 9)

    def help(self, widget):
        logger.debug('clicked help.')
        
    def myMessages(self, widget):
        logger.debug('clicked myMessages.')

    def allMessages(self, widget):
        logger.debug('clicked allMessages.')
        self.layout.remove(self.topBox)
        self.layout.remove(self.bottomBox)

