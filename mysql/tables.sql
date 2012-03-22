CREATE TABLE messages (
  id INTEGER(10) UNSIGNED NOT NULL AUTO_INCREMENT,
  hash VARCHAR(160) DEFAULT NULL,
  device_id int(11) default NULL,
  category_id int(11) default NULL,
  priority_id int(11) default NULL,
  origintime datetime default NULL,
  location varchar(128) default NULL,
  text VARCHAR(512) DEFAULT NULL,
  signedhash VARCHAR(512) DEFAULT NULL,
  public tinyint(1) default 0,
  hopcount int(11) default NULL,
  forwarder_id int(11) default NULL,
  verified tinyint(1) default 0,
  curecount int(11) default NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (id)
);

CREATE TABLE forwarders (
  id int(10) unsigned NOT NULL auto_increment,
  hash VARCHAR(160) DEFAULT NULL,
  device_id int(11) default NULL,
  location varchar(128) default NULL,
  forwardtime datetime default NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
  KEY `hash` (`hash`)
  KEY `device_id` (`device_id`)
);

CREATE TABLE categories (
  id int(10) unsigned NOT NULL auto_increment,
  name VARCHAR(64) DEFAULT NULL,
  description VARCHAR(160) DEFAULT NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
);

CREATE TABLE priorities (
  id int(10) unsigned NOT NULL auto_increment,
  name VARCHAR(64) DEFAULT NULL,
  description VARCHAR(160) DEFAULT NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
);

CREATE TABLE keys (
  id int(10) unsigned NOT NULL auto_increment,
  device_id int(11) default NULL,
  public blob default NULL,
  private blob default NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`),
  KEY `device_id` (`device_id`)
);

CREATE TABLE devices (
  id int(10) unsigned NOT NULL auto_increment,
  uuid VARCHAR(64) DEFAULT NULL,
  make VARCHAR(64) DEFAULT NULL,
  model VARCHAR(64) DEFAULT NULL,
  phone VARCHAR(32) DEFAULT NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
);


CREATE TABLE users (
  id int(10) unsigned NOT NULL auto_increment,
  group_id   int(10) unsigned,
  lastname   varchar(128),
  firstname  varchar(128),
  email    varchar(128),
  active  tinyint(1) unsigned,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
);

CREATE TABLE groups (
  id int(10) unsigned NOT NULL auto_increment,
  name VARCHAR(64) DEFAULT NULL,
  created datetime default NULL,
  modified datetime default NULL,
  PRIMARY KEY  (`id`)
);


