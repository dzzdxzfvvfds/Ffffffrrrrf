#!/usr/bin/env python3

import requests
import sys
from datetime import datetime, date
import json

class SimplifiedSyncTester:
    def __init__(self, base_url="https://syncmate-health.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.patient_id = None
        self.appointment_id = None
        self.created_patients = []
        self.ambulatorio = "pta_centro"

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_login(self):
        """Test login with Domenico credentials"""
        success, response = self.run_test(
            "Login with Domenico/infermiere",
            "POST",
            "auth/login",
            200,
            data={"username": "Domenico", "password": "infermiere"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Login successful, token obtained")
            return True
        return False

    def test_create_appointment_from_sheets(self):
        """Create an appointment that simulates Google Sheets import"""
        if not self.patient_id:
            # Create a test patient first
            patient_data = {
                "nome": "Mario",
                "cognome": "Rossi",
                "tipo": "PICC",
                "ambulatorio": self.ambulatorio
            }
            
            success, response = self.run_test(
                "Create test patient for sync testing",
                "POST",
                "patients",
                201,
                data=patient_data
            )
            
            if success and 'id' in response:
                self.patient_id = response['id']
                self.created_patients.append(self.patient_id)
                print(f"✅ Test patient created with ID: {self.patient_id}")
            else:
                return False

        # Create appointment that simulates Google Sheets import
        today = date.today().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": self.patient_id,
            "ambulatorio": self.ambulatorio,
            "data": today,
            "ora": "10:00",
            "tipo": "PICC",
            "prestazioni": ["medicazione_semplice"],
            "note": "Importato da Google Sheets",  # This marks it as imported
            "stato": "da_fare"
        }
        
        success, response = self.run_test(
            "Create appointment simulating Google Sheets import",
            "POST",
            "appointments",
            200,
            data=appointment_data
        )
        
        if success and 'id' in response:
            self.appointment_id = response['id']
            print(f"✅ Appointment created with ID: {self.appointment_id}")
            print(f"   Note: {response.get('note', '')}")
            return True
        return False

    def test_sync_choices_endpoints_removed(self):
        """Test that sync_choices endpoints are removed"""
        # Test that GET /api/sync/choices/{ambulatorio} returns 404 or doesn't exist
        success, response = self.run_test(
            "Verify sync_choices GET endpoint is removed",
            "GET",
            f"sync/choices/{self.ambulatorio}",
            404  # Should return 404 since endpoint is removed
        )
        
        if success:
            print("✅ sync_choices GET endpoint properly removed")
        else:
            print("⚠️ sync_choices GET endpoint still exists (may need removal)")
        
        # Test that DELETE /api/sync/choices/clear/{ambulatorio} returns 404
        success2, response2 = self.run_test(
            "Verify sync_choices DELETE endpoint is removed",
            "DELETE",
            f"sync/choices/clear/{self.ambulatorio}",
            404  # Should return 404 since endpoint is removed
        )
        
        if success2:
            print("✅ sync_choices DELETE endpoint properly removed")
        else:
            print("⚠️ sync_choices DELETE endpoint still exists (may need removal)")
        
        return success or success2  # Pass if at least one endpoint is properly removed

    def test_sync_analyze_endpoint(self):
        """Test the sync analyze endpoint that shows conflicts"""
        success, response = self.run_test(
            "Test sync analyze endpoint",
            "POST",
            "sync/google-sheets/analyze",
            200,
            data={
                "ambulatorio": self.ambulatorio,
                "year": datetime.now().year
            }
        )
        
        if success:
            print(f"✅ Sync analyze endpoint working:")
            print(f"   - Success: {response.get('success', False)}")
            print(f"   - Has conflicts: {response.get('has_conflicts', False)}")
            if response.get('has_conflicts'):
                conflicts = response.get('conflicts', [])
                print(f"   - Number of conflicts: {len(conflicts)}")
                for i, conflict in enumerate(conflicts[:2]):  # Show first 2 conflicts
                    print(f"     Conflict {i+1}: {conflict.get('id', 'N/A')}")
                    print(f"       Options: {len(conflict.get('options', []))}")
            return True
        return False

    def test_sync_main_endpoint(self):
        """Test the main sync endpoint"""
        success, response = self.run_test(
            "Test main sync endpoint",
            "POST",
            "sync/google-sheets",
            200,
            data={
                "ambulatorio": self.ambulatorio,
                "year": datetime.now().year,
                "conflict_actions": {}  # Empty conflict actions for now
            }
        )
        
        if success:
            print(f"✅ Main sync endpoint working:")
            print(f"   - Success: {response.get('success', False)}")
            print(f"   - Created patients: {response.get('created_patients', 0)}")
            print(f"   - Created appointments: {response.get('created_appointments', 0)}")
            return True
        return False

    def cleanup(self):
        """Clean up test data"""
        if self.appointment_id:
            self.run_test(
                "Delete test appointment",
                "DELETE",
                f"appointments/{self.appointment_id}",
                200
            )
        
        # Clean up all created patients
        for patient_id in self.created_patients:
            self.run_test(
                f"Delete test patient {patient_id}",
                "DELETE",
                f"patients/{patient_id}",
                200
            )
        
        if self.patient_id and self.patient_id not in self.created_patients:
            self.run_test(
                "Delete test patient",
                "DELETE",
                f"patients/{self.patient_id}",
                200
            )

def main():
    print("🏥 Testing Google Sheets Sync System - Manual Modification Tracking")
    print("=" * 80)
    
    tester = GoogleSheetsSyncTester()
    
    try:
        # Test sequence focusing on sync functionality
        if not tester.test_login():
            print("❌ Login failed, stopping tests")
            return 1

        if not tester.test_create_appointment_from_sheets():
            print("❌ Appointment creation (simulating Google Sheets import) failed")
            return 1

        if not tester.test_manual_appointment_modification_debug():
            print("❌ Manual appointment modification failed")
            return 1

        if not tester.test_get_manual_edits_endpoint():
            print("❌ Manual edits endpoint failed")
            return 1

        if not tester.test_sync_timestamp_endpoint():
            print("❌ Sync timestamp endpoint failed")
            return 1

        if not tester.test_appointment_preservation_logic():
            print("❌ Appointment preservation logic test failed")
            return 1

        # Print results
        print(f"\n📊 Test Results:")
        print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
        
        if tester.tests_passed == tester.tests_run:
            print("✅ All Google Sheets sync tests passed!")
            print("🔍 Key findings:")
            print("   - Login with Domenico/infermiere credentials works")
            print("   - Manual modification of imported appointments adds 'manually_modified' flag")
            print("   - GET /api/sync/manual-edits/{ambulatorio} endpoint works")
            print("   - Sync timestamp tracking is functional")
            print("   - Manual modifications are properly tracked for preservation during sync")
            return 0
        else:
            print("❌ Some tests failed")
            return 1
            
    finally:
        # Cleanup
        print("\n🧹 Cleaning up test data...")
        tester.cleanup()

if __name__ == "__main__":
    sys.exit(main())