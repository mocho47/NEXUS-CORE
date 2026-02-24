'use strict';

/**
 * @class NexusDB
 * @description A class to manage database operations in a clean and modular way.
 */
class NexusDB {
    constructor(database) {
        if (!database || typeof database !== 'object') {
            throw new Error('A valid database object must be provided.');
        }
        this.database = database;
    }

    /**
     * @function create
     * @description Create a new entry in the database.
     * @param {string} key - The key for the entry.
     * @param {any} value - The value of the entry.
     * @throws Will throw an error if the key or value is invalid.
     */
    create(key, value) {
        this.validateKey(key);
        this.validateValue(value);
        this.database[key] = value;
    }

    /**
     * @function read
     * @description Read an entry from the database.
     * @param {string} key - The key for the entry.
     * @returns {any} The value of the entry.
     * @throws Will throw an error if the key is invalid or not found.
     */
    read(key) {
        this.validateKey(key);
        if (!(key in this.database)) {
            throw new Error(`Key '${key}' not found in the database.`);
        }
        return this.database[key];
    }

    /**
     * @function update
     * @description Update an existing entry in the database.
     * @param {string} key - The key for the entry.
     * @param {any} newValue - The new value to update.
     * @throws Will throw an error if the key is invalid or not found.
     */
    update(key, newValue) {
        this.validateKey(key);
        if (!(key in this.database)) {
            throw new Error(`Key '${key}' not found in the database.`);
        }
        this.validateValue(newValue);
        this.database[key] = newValue;
    }

    /**
     * @function delete
     * @description Delete an entry from the database.
     * @param {string} key - The key for the entry to delete.
     * @throws Will throw an error if the key is invalid or not found.
     */
    delete(key) {
        this.validateKey(key);
        if (!(key in this.database)) {
            throw new Error(`Key '${key}' not found in the database.`);
        }
        delete this.database[key];
    }

    /**
     * @function validateKey
     * @description Validate the key.
     * @param {string} key - The key to validate.
     * @throws Will throw an error if the key is invalid.
     */
    validateKey(key) {
        if (typeof key !== 'string' || !key.trim()) {
            throw new Error('Key must be a non-empty string.');
        }
    }

    /**
     * @function validateValue
     * @description Validate the value.
     * @param {any} value - The value to validate.
     * @throws Will throw an error if the value is invalid.
     */
    validateValue(value) {
        // Add custom validation logic as needed
        if (value === undefined || value === null) {
            throw new Error('Value must not be null or undefined.');
        }
    }
}

// Example usage:
const db = new NexusDB({});
db.create('key1', 'value1');
console.log(db.read('key1')); // Output: 'value1'

