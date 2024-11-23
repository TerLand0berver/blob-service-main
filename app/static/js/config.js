// config.js - Configuration management module
import api from './api.js';

class Config {
    constructor() {
        this.config = null;
    }

    // Load configuration
    async load() {
        try {
            const response = await api.get('/api/config');
            if (response.success) {
                this.config = response.data;
                this._updateForm();
                return true;
            }
            api.showMessage(response.message || 'Failed to load configuration', true);
            return false;
        } catch (error) {
            api.showMessage('Failed to load configuration: ' + error.message, true);
            return false;
        }
    }

    // Save configuration
    async save() {
        try {
            const newConfig = {
                auth: {
                    admin_user: document.getElementById('admin_user').value || 'root',
                    admin_password: document.getElementById('admin_password').value || 'root123456',
                    require_auth: document.getElementById('require_auth').checked,
                    whitelist_domains: document.getElementById('whitelist_domains').value.split(',').filter(x => x),
                    whitelist_ips: document.getElementById('whitelist_ips').value.split(',').filter(x => x)
                },
                storage: {
                    type: document.getElementById('storage_type').value,
                    local: {
                        root_dir: document.getElementById('local_storage_path').value,
                        domain: document.getElementById('local_storage_domain').value
                    },
                    s3: {
                        access_key: document.getElementById('s3_access_key').value,
                        secret_key: document.getElementById('s3_secret_key').value,
                        bucket_name: document.getElementById('s3_bucket_name').value,
                        endpoint_url: document.getElementById('s3_endpoint_url').value,
                        region_name: document.getElementById('s3_region_name').value
                    }
                },
                features: {
                    enable_ocr: document.getElementById('enable_ocr').checked,
                    enable_vision: document.getElementById('enable_vision').checked,
                    enable_azure_speech: document.getElementById('enable_azure_speech').checked,
                    ocr_languages: document.getElementById('ocr_languages').value.split(',').filter(x => x),
                    vision_api_key: document.getElementById('vision_api_key').value,
                    azure_speech_key: document.getElementById('azure_speech_key').value,
                    azure_speech_region: document.getElementById('azure_speech_region').value
                },
                limits: {
                    max_file_size: parseInt(document.getElementById('max_file_size').value) || 10,
                    allowed_extensions: document.getElementById('allowed_extensions').value.split(',').filter(x => x),
                    max_ocr_size: parseInt(document.getElementById('max_ocr_size').value) || 5,
                    max_vision_size: parseInt(document.getElementById('max_vision_size').value) || 5,
                    max_speech_size: parseInt(document.getElementById('max_speech_size').value) || 10
                },
                server: {
                    host: document.getElementById('server_host').value || '0.0.0.0',
                    port: parseInt(document.getElementById('server_port').value) || 8000,
                    debug: document.getElementById('server_debug').checked,
                    cors_origins: document.getElementById('cors_origins').value.split(',').filter(x => x),
                    log_level: document.getElementById('log_level').value || 'info',
                    request_timeout: parseInt(document.getElementById('request_timeout').value) || 30
                }
            };

            const response = await api.post('/api/config', newConfig);
            if (response.success) {
                this.config = newConfig;
                api.showMessage('Configuration saved successfully');
                return true;
            }
            
            api.showMessage(response.message || 'Failed to save configuration', true);
            return false;
        } catch (error) {
            api.showMessage('Failed to save configuration: ' + error.message, true);
            return false;
        }
    }

    // Update form with current configuration
    _updateForm() {
        if (!this.config) return;

        // Auth settings
        document.getElementById('admin_user').value = this.config.auth?.admin_user || '';
        document.getElementById('admin_password').value = this.config.auth?.admin_password || '';
        document.getElementById('require_auth').checked = this.config.auth?.require_auth ?? true;
        document.getElementById('whitelist_domains').value = (this.config.auth?.whitelist_domains || []).join(',');
        document.getElementById('whitelist_ips').value = (this.config.auth?.whitelist_ips || []).join(',');

        // Storage settings
        document.getElementById('storage_type').value = this.config.storage?.type || 'local';
        document.getElementById('local_storage_path').value = this.config.storage?.local?.root_dir || '';
        document.getElementById('local_storage_domain').value = this.config.storage?.local?.domain || '';
        document.getElementById('s3_access_key').value = this.config.storage?.s3?.access_key || '';
        document.getElementById('s3_secret_key').value = this.config.storage?.s3?.secret_key || '';
        document.getElementById('s3_bucket_name').value = this.config.storage?.s3?.bucket_name || '';
        document.getElementById('s3_endpoint_url').value = this.config.storage?.s3?.endpoint_url || '';
        document.getElementById('s3_region_name').value = this.config.storage?.s3?.region_name || '';

        // Feature settings
        document.getElementById('enable_ocr').checked = this.config.features?.enable_ocr ?? false;
        document.getElementById('enable_vision').checked = this.config.features?.enable_vision ?? false;
        document.getElementById('enable_azure_speech').checked = this.config.features?.enable_azure_speech ?? false;
        document.getElementById('ocr_languages').value = (this.config.features?.ocr_languages || []).join(',');
        document.getElementById('vision_api_key').value = this.config.features?.vision_api_key || '';
        document.getElementById('azure_speech_key').value = this.config.features?.azure_speech_key || '';
        document.getElementById('azure_speech_region').value = this.config.features?.azure_speech_region || '';

        // Limit settings
        document.getElementById('max_file_size').value = this.config.limits?.max_file_size || 10;
        document.getElementById('allowed_extensions').value = (this.config.limits?.allowed_extensions || []).join(',');
        document.getElementById('max_ocr_size').value = this.config.limits?.max_ocr_size || 5;
        document.getElementById('max_vision_size').value = this.config.limits?.max_vision_size || 5;
        document.getElementById('max_speech_size').value = this.config.limits?.max_speech_size || 10;

        // Server settings
        document.getElementById('server_host').value = this.config.server?.host || '0.0.0.0';
        document.getElementById('server_port').value = this.config.server?.port || 8000;
        document.getElementById('server_debug').checked = this.config.server?.debug ?? false;
        document.getElementById('cors_origins').value = (this.config.server?.cors_origins || []).join(',');
        document.getElementById('log_level').value = this.config.server?.log_level || 'info';
        document.getElementById('request_timeout').value = this.config.server?.request_timeout || 30;

        // Update storage settings visibility
        this._updateStorageSettings();
    }

    // Update storage settings visibility
    _updateStorageSettings() {
        const storageType = document.getElementById('storage_type').value;
        document.getElementById('local_storage_settings').style.display = storageType === 'local' ? 'block' : 'none';
        document.getElementById('s3_storage_settings').style.display = storageType === 's3' ? 'block' : 'none';
    }
}

export default new Config();
