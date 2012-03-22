<?php defined('SYSPATH') or die('No direct script access.');
/**
 * Disaster  - Load All Events
 *
 * PHP version 5
 * LICENSE: This source file is subject to LGPL license 
 * that is available through the world-wide-web at the following URI:
 * http://www.gnu.org/copyleft/lesser.html
 * @author	   Ushahidi Team <team@ushahidi.com> 
 * @author	   Don Voita <don@cs.ucsb.edu>
 * @author	   Danny Iland <iland@cs.ucsb.edu>
 * @package	   Ushahidi - http://source.ushahididev.com
 * @copyright  Ushahidi - http://www.ushahidi.com
 * @license	   http://www.gnu.org/copyleft/lesser.html GNU Lesser General Public License (LGPL) 
 */

class disasterevents {
	
	
	//protected $table_prefix;
	protected $message_hash;

    /**
     * Adds all the events to the main Ushahidi application
     */
	public function __construct()
	{
		Event::add('system.pre_controller', array($this, 'add'));
	}

    public function debug($var)
    {
        echo "<pre>";
        print_r($var);
        "</pre>"; 
    }
    /**
     * Registers the main event add method
     */
	public function add()
	{
		Event::add('ushahidi_action.report_submit_api',  array($this, 'set_message_hash'));
		Event::add('ushahidi_action.report_edit_api',  array($this, 'save_message_hash'));
	}
	
	public function set_message_hash()
	{
        // The incident is in Event::$data
        $post = Event::$data;
        $this->message_hash = $post->hash;
        $this->log($this->message_hash);
	}

	public function save_message_hash()
	{
        // The incident is in Event::$data
        $incident = Event::$data;
        $this->incident_id = $incident->id;
        
        Disaster_Cure_Model::save_cure($this->incident_id, $this->message_hash);
	}

    public function log($message)
    {
        $message = date("Y-m-d H:i:s")." : ".serialize($message);
        $message .= "\n";
        $logfile = DOCROOT."application/logs/olpc.log";
        $logfile = fopen($logfile, 'a+');
        fwrite($logfile, $message);
        fclose($logfile);
    }
}
new disasterevents;
