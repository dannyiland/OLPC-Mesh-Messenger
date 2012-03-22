<?php defined('SYSPATH') or die('No direct script access.');
/**
 * Disaster_Cure Model
 *
 * PHP version 5
 */

class Disaster_Cure_Model extends ORM
{
	// Database table name
	protected $table_name = 'disaster_cure';

    /**
     * Gets the cures that match the conditions specified in the $where parameter
     * The conditions must relate to columns in the cures table
     *
     * @param array $where List of conditions to apply to the query
     * @param mixed $limit No. of records to fetch or an instance of Pagination
     * @param string $order_field Column by which to order the records
     * @param string $sort How to order the records - only ASC or DESC are allowed
     * @return Database_Result
     */
    public static function get_cures($where = array(), $limit = NULL, $order_field = NULL, $sort = NULL)
    {
        // Get the table prefix
        $table_prefix = Kohana::config('database.default.table_prefix');

        // Query
        $sql = 'SELECT DISTINCT cures.hash, cures.created ';
        $sql .= 'FROM '.$table_prefix. 'disaster_cure' . ' cures ';

        // Check for the order field and sort parameters
        //$sql .= 'ORDER BY cures.created DESC ';

        if(!empty($limit) && is_int($limit) && intval($limit) > 0) {
            $sql .= 'LIMIT  0, '.$limit;
        }

        //Kohana::log('debug', $sql);
        // Database instance for the query
        $db = new Database();
        // Return
        return $db->query($sql);    
    }

    public static function save_cure($incident_id = NULL, $hash = NULL) 
    {
        // TODO actual validation: should be done as part of the hook, not here.
        if (empty($incident_id) || empty($hash)) {
            return false;
        }

        $table_prefix = Kohana::config('database.default.table_prefix');

        $sql = 'INSERT IGNORE INTO ';
        $sql .= $table_prefix . 'disaster_cure ';
        $sql .= '(incident_id, hash, created) VALUES (?, ?, ?)';

        $db = new Database;
        $now = new DateTime();
        return $db->query($sql, $incident_id, $hash, $now->format('Y-m-d H:i:s')); 
    }
}
