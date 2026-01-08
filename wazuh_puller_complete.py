#!/usr/bin/env python3
"""
Complete Wazuh API Puller for Production
"""
import requests
import zipfile
import tempfile
import shutil
import os
import sys
import json
import time
from pathlib import Path
import subprocess
from datetime import datetime

class WazuhAPIPuller:
    def __init__(self, config_path="/etc/wazuh/api_puller.json"):
        self.config = self.load_config(config_path)
        self.api_url = self.config['api_url'].rstrip('/')
        self.api_key = self.config['api_key']
        self.server_id = self.config['server_id']
        
        # Wazuh directories
        self.rules_dir = Path("/var/ossec/etc/rules")
        self.decoders_dir = Path("/var/ossec/etc/decoders")
        self.backup_dir = Path("/var/ossec/backups")
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"Wazuh-Puller/{self.server_id}"
        }
        
        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def load_config(self, config_path):
        """Load configuration file"""
        default_config = {
            "api_url": "http://localhost:8000",
            "api_key": "",
            "server_id": "unknown",
            "create_backup": True,
            "restart_wazuh": True,
            "verify_ssl": False
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def create_backup(self):
        """Create backup of current rules and decoders"""
        if not self.config['create_backup']:
            return True
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        try:
            print(f"Creating backup at: {backup_path}")
            
            # Backup rules
            if self.rules_dir.exists():
                rules_backup = backup_path / "rules"
                rules_backup.mkdir(parents=True, exist_ok=True)
                for xml_file in self.rules_dir.glob("*.xml"):
                    shutil.copy2(xml_file, rules_backup / xml_file.name)
            
            # Backup decoders
            if self.decoders_dir.exists():
                decoders_backup = backup_path / "decoders"
                decoders_backup.mkdir(parents=True, exist_ok=True)
                for xml_file in self.decoders_dir.glob("*.xml"):
                    shutil.copy2(xml_file, decoders_backup / xml_file.name)
            
            print(f"✅ Backup created successfully")
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def test_connection(self):
        """Test API connection"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                headers=self.headers,
                timeout=10,
                verify=self.config['verify_ssl']
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Connection: {data.get('status', 'unknown')}")
                return True
            else:
                print(f"❌ API Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API Connection error: {e}")
            return False
    
    def get_rules_info(self):
        """Get information about available rules"""
        try:
            response = requests.get(
                f"{self.api_url}/api/rules/list",
                headers=self.headers,
                timeout=30,
                verify=self.config['verify_ssl']
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get rules info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Rules info error: {e}")
            return None
    
    def download_package(self):
        """Download rules package from API"""
        try:
            print(f"Downloading rules package from {self.api_url}...")
            
            response = requests.get(
                f"{self.api_url}/api/rules/package",
                headers=self.headers,
                stream=True,
                timeout=60,
                verify=self.config['verify_ssl']
            )
            
            if response.status_code == 200:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                
                file_size = os.path.getsize(temp_file.name)
                print(f"✅ Downloaded: {file_size:,} bytes")
                return temp_file.name
            else:
                print(f"❌ Download failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None
    
    def extract_package(self, zip_path):
        """Extract zip package to temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp(prefix="wazuh_rules_")
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            print(f"✅ Extracted to: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            print(f"❌ Extraction error: {e}")
            return None
    
    def deploy_files(self, extract_dir):
        """Deploy extracted files to Wazuh directories"""
        try:
            extract_path = Path(extract_dir)
            rules_deployed = 0
            decoders_deployed = 0
            
            # Deploy rules
            rules_source = extract_path / "rules"
            if rules_source.exists():
                # Clear existing rules
                for xml_file in self.rules_dir.glob("*.xml"):
                    xml_file.unlink()
                
                # Copy new rules
                for xml_file in rules_source.glob("*.xml"):
                    shutil.copy2(xml_file, self.rules_dir / xml_file.name)
                    rules_deployed += 1
            
            # Deploy decoders
            decoders_source = extract_path / "decoders"
            if decoders_source.exists():
                # Clear existing decoders
                for xml_file in self.decoders_dir.glob("*.xml"):
                    xml_file.unlink()
                
                # Copy new decoders
                for xml_file in decoders_source.glob("*.xml"):
                    shutil.copy2(xml_file, self.decoders_dir / xml_file.name)
                    decoders_deployed += 1
            
            # Set proper permissions
            subprocess.run(["chown", "-R", "root:wazuh", str(self.rules_dir)], check=False)
            subprocess.run(["chown", "-R", "root:wazuh", str(self.decoders_dir)], check=False)
            subprocess.run(["chmod", "-R", "640", str(self.rules_dir)], check=False)
            subprocess.run(["chmod", "-R", "640", str(self.decoders_dir)], check=False)
            
            print(f"✅ Deployed: {rules_deployed} rules, {decoders_deployed} decoders")
            return rules_deployed + decoders_deployed > 0
            
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
    
    def restart_wazuh(self):
        """Restart Wazuh manager service"""
        if not self.config['restart_wazuh']:
            return True
        
        try:
            print("Restarting Wazuh manager...")
            result = subprocess.run(
                ["systemctl", "restart", "wazuh-manager"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Wazuh manager restarted successfully")
                return True
            else:
                print(f"❌ Wazuh restart failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Restart error: {e}")
            return False
    
    def report_deployment(self, success, file_count=0, error=""):
        """Report deployment status back to API"""
        try:
            report_data = {
                "server_id": self.server_id,
                "success": success,
                "file_count": file_count,
                "error": error,
                "timestamp": datetime.now().isoformat()
            }
            
            # This would be a POST to your API's deployment endpoint
            # For now, just log it
            print(f"📊 Deployment Report: {json.dumps(report_data, indent=2)}")
            
            # Save to local log
            log_file = Path("/var/log/wazuh/api_puller.log")
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(log_file, 'a') as f:
                f.write(json.dumps(report_data) + "\n")
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to log deployment: {e}")
            return False
    
    def run(self):
        """Main execution method"""
        print(f"\n{'='*60}")
        print(f"WAZUH RULES UPDATE - {self.server_id}")
        print(f"{'='*60}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"API Server: {self.api_url}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        # Step 1: Test connection
        if not self.test_connection():
            self.report_deployment(False, 0, "API connection failed")
            return False
        
        # Step 2: Get rules info
        rules_info = self.get_rules_info()
        if not rules_info:
            self.report_deployment(False, 0, "Failed to get rules info")
            return False
        
        print(f"📁 Available: {rules_info.get('counts', {}).get('rules', 0)} rules, "
              f"{rules_info.get('counts', {}).get('decoders', 0)} decoders")
        
        # Step 3: Create backup
        if not self.create_backup():
            print("⚠️  Backup failed, continuing anyway...")
        
        # Step 4: Download package
        zip_path = self.download_package()
        if not zip_path:
            self.report_deployment(False, 0, "Download failed")
            return False
        
        # Step 5: Extract package
        extract_dir = self.extract_package(zip_path)
        if not extract_dir:
            self.report_deployment(False, 0, "Extraction failed")
            return False
        
        # Step 6: Deploy files
        deployment_success = self.deploy_files(extract_dir)
        
        # Step 7: Restart Wazuh if files were deployed
        if deployment_success:
            restart_success = self.restart_wazuh()
            overall_success = deployment_success and restart_success
        else:
            overall_success = False
        
        # Step 8: Cleanup
        try:
            os.unlink(zip_path)
            shutil.rmtree(extract_dir, ignore_errors=True)
        except:
            pass
        
        # Step 9: Report
        elapsed = time.time() - start_time
        self.report_deployment(
            overall_success,
            rules_info.get('counts', {}).get('total', 0),
            "" if overall_success else "Deployment or restart failed"
        )
        
        print(f"\n{'='*60}")
        if overall_success:
            print(f"✅ UPDATE COMPLETE - Success in {elapsed:.1f} seconds")
        else:
            print(f"❌ UPDATE FAILED - Check logs for details")
        print(f"{'='*60}")
        
        return overall_success

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Wazuh API Puller")
    parser.add_argument("--config", default="/etc/wazuh/api_puller.json",
                       help="Configuration file path")
    parser.add_argument("--test", action="store_true",
                       help="Test mode - check connection only")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run - don't make changes")
    
    args = parser.parse_args()
    
    puller = WazuhAPIPuller(args.config)
    
    if args.test:
        print("🧪 TEST MODE - Checking connectivity")
        return 0 if puller.test_connection() else 1
    elif args.dry_run:
        print("🌵 DRY RUN - Simulating deployment")
        rules_info = puller.get_rules_info()
        if rules_info:
            print(f"Would deploy: {rules_info.get('counts', {}).get('total', 0)} files")
            return 0
        else:
            return 1
    else:
        success = puller.run()
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
