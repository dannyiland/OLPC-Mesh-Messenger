<?php defined('SYSPATH') or die('No direct script access.');
/**
 * Disaster_Api_Object
 *
 * This class handles Viddler video API functions
 *
 * PHP version 5
*/

class Cure_Api_Object extends Api_Object_Core {

    protected $action;

    public function __construct($api_service)
    {
        parent::__construct($api_service);
    }

    /**
     * Implementation of abstract method declared in superclass
     */
    public function perform_task()
    {   
        $this->action = '';
        if (isset($this->request['action'])) {
            $this->action = $this->request['action'];
        }

        switch ($this->action){
                
                // Get videos for a report or all reports
                case 'get':
                    $ret_value = $this->_get_cures();
                break;
                
                // Proper action not set
                default:
                    // System information mainly obtained through use of callback
                    // Therefore set the default response to "not found"
                    $ret_value = 999;
        }
        //$this->response_data =  $this->response($ret_value);
        $this->response_data =  $ret_value;
    }

    /**
     * Generic function to get cures by given set of parameters
     * - Currently just get all is implemented
     *
     * @param string $where SQL where clause
     * @return string XML or JSON string
     */

    private function _get_cures($where = array())
    {
        $cures = Disaster_Cure_Model::get_cures($where, NULL, NULL, NULL);

        // No records found.
        if ($cures->count() == 0) {
            return $this->response(4, $this->error_messages);
        }

        // Found cures
        $this->record_count = $cures->count();

        $json_cures = array();
        
        foreach ($cures as $cure) {
            // XML ?
            if ($this->response_type == 'json') {
                $json_cures[] = array(
                        "hash" => $cure->hash,
                        "created" => $cure->created,
                );
            }
        }
        
        // Create the JSON array
        $data = array(
            "payload" => array(
                "domain" => $this->domain,
                "cures" => $json_cures
            ),
            "error" => $this->api_service->get_error_msg(0)
        );
    
        $this->log($cures);
        if ($this->response_type == 'json') {
            return $this->array_as_json($data);
        }
    }

    public function log($message)
    {
        $message = date("Y-m-d H:i:s")." : ".serialize($message);
        $message .= "\n";
        $logfile = DOCROOT."application/logs/olpcCures.log";
        $logfile = fopen($logfile, 'a+');
        fwrite($logfile, $message);
        fclose($logfile);
    }

}
