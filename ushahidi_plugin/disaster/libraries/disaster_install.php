<?php
/**
 * Performs install/uninstall methods for the Disaster plugin
 *
 * PHP version 5
 */

class Disaster_Install {

	/**
	 * Constructor to load the shared database library
	 */
	public function __construct()
	{
		$this->db = Database::instance();
	}

	/**
	 * Creates the required database tables for the smssync plugin
	 */
	public function run_install()
	{
		// Create the database tables.
		// Also include table_prefix in name
		$this->db->query("
			CREATE TABLE IF NOT EXISTS `".Kohana::config('database.default.table_prefix')."disaster_cure` (
				id int(11) unsigned NOT NULL AUTO_INCREMENT,
                incident_id bigint(20) DEFAULT NULL,
				hash varchar(128) DEFAULT NULL,
                created datetime DEFAULT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `hash` (`hash`)
			);
		");
	}

	/**
	 * Deletes the database tables for the actionable module
	 */
	public function uninstall()
	{
		$this->db->query('DROP TABLE `'.Kohana::config('database.default.table_prefix').'disaster_cure`');
	}
}
