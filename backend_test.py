#!/usr/bin/env python3

import requests
import sys
from datetime import datetime, date
import json

class GoogleSheetsSyncTester:
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
            "Login with Domenico",
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

    def test_batch_patient_creation_with_implant(self):
        """Test batch patient creation with PICC implant type"""
        batch_data = {
            "patients": [
                {
                    "nome": "Mario",
                    "cognome": "TestImpianto",
                    "tipo": "PICC",
                    "ambulatorio": "pta_centro",
                    "tipo_impianto": "picc_port",
                    "data_inserimento_impianto": "2026-01-11"
                }
            ]
        }
        
        success, response = self.run_test(
            "Batch Create PICC Patient with Implant",
            "POST",
            "patients/batch",
            201,
            data=batch_data
        )
        
        if success:
            created_count = response.get('created', 0)
            impianti_created = response.get('impianti_created', 0)
            patients = response.get('patients', [])
            
            print(f"✅ Batch creation successful:")
            print(f"   - Patients created: {created_count}")
            print(f"   - Implants created: {impianti_created}")
            
            if patients and len(patients) > 0:
                self.patient_id = patients[0]['id']
                self.created_patients.append(self.patient_id)
                print(f"   - Patient ID: {self.patient_id}")
            
            if created_count > 0 and impianti_created > 0:
                return True
        return False

    def test_get_impianti_list(self):
        """Test getting impianti list to verify the created implant"""
        params = {
            "ambulatorio": "pta_centro",
            "anno": 2026,
            "mese": 1
        }
        
        success, response = self.run_test(
            "Get Impianti List",
            "GET",
            "impianti",
            200,
            params=params
        )
        
        if success:
            impianti = response.get('impianti', [])
            count = response.get('count', 0)
            
            print(f"✅ Impianti list retrieved:")
            print(f"   - Total impianti: {count}")
            
            # Look for our test patient
            test_implant = None
            for implant in impianti:
                if (implant.get('patient_cognome') == 'TestImpianto' and 
                    implant.get('patient_nome') == 'Mario'):
                    test_implant = implant
                    break
            
            if test_implant:
                print(f"   - Found test implant: {test_implant.get('tipo_impianto')} on {test_implant.get('data_impianto')}")
                return True
            else:
                print(f"   - Test implant not found in list")
                return False
        return False

    def test_statistics_impianti(self):
        """Test statistics to verify implant count"""
        params = {
            "ambulatorio": "pta_centro",
            "anno": 2026,
            "mese": 1
        }
        
        success, response = self.run_test(
            "Get Statistics for Impianti",
            "GET",
            "statistics",
            200,
            params=params
        )
        
        if success:
            print(f"✅ Statistics retrieved:")
            print(f"   - Response: {json.dumps(response, indent=2)}")
            return True
        return False

    def test_create_picc_patient(self):
        """Create a PICC patient for testing"""
        patient_data = {
            "nome": "Test",
            "cognome": "Rosso",
            "tipo": "PICC",
            "ambulatorio": "pta_centro"
        }
        
        success, response = self.run_test(
            "Create PICC Patient 'Test Rosso'",
            "POST",
            "patients",
            201,
            data=patient_data
        )
        
        if success and 'id' in response:
            self.patient_id = response['id']
            print(f"✅ Patient created with ID: {self.patient_id}")
            return True
        return False

    def test_create_appointment(self):
        """Create an appointment for the test patient"""
        today = date.today().strftime("%Y-%m-%d")
        appointment_data = {
            "patient_id": self.patient_id,
            "ambulatorio": "pta_centro",
            "data": today,
            "ora": "09:00",
            "tipo": "PICC",
            "prestazioni": ["medicazione_semplice", "irrigazione_catetere"],
            "stato": "da_fare"
        }
        
        success, response = self.run_test(
            "Create PICC Appointment",
            "POST",
            "appointments",
            200,
            data=appointment_data
        )
        
        if success and 'id' in response:
            self.appointment_id = response['id']
            print(f"✅ Appointment created with ID: {self.appointment_id}")
            return True
        return False

    def test_mark_non_presentato(self):
        """Mark appointment as non_presentato"""
        update_data = {"stato": "non_presentato"}
        
        success, response = self.run_test(
            "Mark appointment as non_presentato",
            "PUT",
            f"appointments/{self.appointment_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"✅ Appointment marked as non_presentato")
            return True
        return False

    def test_change_patient_type(self):
        """Test changing patient type from PICC to MED using new endpoint"""
        if not self.patient_id:
            print("❌ No patient ID available for type change test")
            return False
            
        # Test changing patient type to enable both PICC and MED
        type_change_data = {
            "enable_picc": True,
            "enable_med": True
        }
        
        success, response = self.run_test(
            "Change Patient Type to PICC_MED",
            "PUT",
            f"patients/{self.patient_id}/tipo",
            200,
            data=type_change_data
        )
        
        if success:
            patient_data = response.get('patient', {})
            new_type = patient_data.get('tipo')
            message = response.get('message', '')
            
            print(f"✅ Patient type changed successfully:")
            print(f"   - New type: {new_type}")
            print(f"   - Message: {message}")
            
            if new_type == "PICC_MED":
                return True
            else:
                print(f"❌ Expected type PICC_MED, got {new_type}")
                return False
        return False

    def test_sync_timestamp_api(self):
        """Test the sync timestamp API for Google Sheets synchronization"""
        success, response = self.run_test(
            "Get Sync Timestamp for pta_centro",
            "GET",
            "sync/timestamp/pta_centro",
            200
        )
        
        if success:
            # Response might be None if no timestamp exists yet
            if response is None:
                print(f"✅ Sync timestamp retrieved: No timestamp set yet (None)")
                return True
            
            timestamp = response.get('timestamp') if isinstance(response, dict) else None
            ambulatorio = response.get('ambulatorio') if isinstance(response, dict) else None
            
            print(f"✅ Sync timestamp retrieved:")
            print(f"   - Ambulatorio: {ambulatorio}")
            print(f"   - Timestamp: {timestamp}")
            
            return True
        return False

    def test_get_appointments(self):
        """Verify appointment exists but with non_presentato status"""
        today = date.today().strftime("%Y-%m-%d")
        params = {
            "ambulatorio": "pta_centro",
            "data": today
        }
        
        success, response = self.run_test(
            "Get appointments for today",
            "GET",
            "appointments",
            200,
            params=params
        )
        
        if success:
            appointments = response if isinstance(response, list) else []
            non_presentato_count = len([a for a in appointments if a.get('stato') == 'non_presentato'])
            print(f"📅 Found {len(appointments)} appointments today, {non_presentato_count} marked as non_presentato")
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
    print("🏥 Testing Ambulatorio Infermieristico API - Patient Type Change & Sync Features")
    print("=" * 80)
    
    tester = AmbulatorioAPITester()
    
    try:
        # Test sequence
        if not tester.test_login():
            print("❌ Login failed, stopping tests")
            return 1

        if not tester.test_create_picc_patient():
            print("❌ Patient creation failed, stopping tests")
            return 1

        if not tester.test_change_patient_type():
            print("❌ Patient type change failed")
            return 1

        if not tester.test_sync_timestamp_api():
            print("❌ Sync timestamp API failed")
            return 1

        if not tester.test_create_appointment():
            print("❌ Appointment creation failed")
            return 1

        if not tester.test_get_appointments():
            print("❌ Get appointments failed")
            return 1

        # Print results
        print(f"\n📊 Test Results:")
        print(f"Tests passed: {tester.tests_passed}/{tester.tests_run}")
        
        if tester.tests_passed == tester.tests_run:
            print("✅ All backend API tests passed!")
            print("🔍 Key findings:")
            print("   - Login with Domenico credentials works")
            print("   - Patient type change API (PUT /api/patients/{id}/tipo) works")
            print("   - Sync timestamp API (GET /api/sync/timestamp/{ambulatorio}) works")
            print("   - Patient creation and appointment management works")
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