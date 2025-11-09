import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_tools():
    """Test básico de herramientas individuales"""
    try:
        print("🔧 Testing contract tools individually...")
        
        # Test 1: Importar herramientas
        from agents.contract_management.tools import contract_generator_tool
        print("✅ Contract generator tool imported")
        
        # Test 2: Datos básicos
        employee_data = {
            "employee_id": "TEST_001",
            "first_name": "Test",
            "last_name": "User",
            "position": "Engineer",
            "department": "IT"
        }
        
        it_credentials = {
            "username": "test.user",
            "email": "test.user@company.com"
        }
        
        contractual_data = {
            "start_date": "2025-12-01",
            "salary": 50000,
            "currency": "USD"
        }
        
        print("✅ Test data prepared")
        
        # Test 3: Invocar herramienta directamente
        print("🚀 Invoking contract generator...")
        
        # Intentar diferentes formas de invocación
        try:
            # Forma 1: Parámetros directos
            result1 = contract_generator_tool.invoke(
                employee_data, it_credentials, contractual_data, "v2024.1"
            )
            print(f"✅ Direct params: {result1.get('success', False)}")
        except Exception as e:
            print(f"❌ Direct params failed: {e}")
        
        try:
            # Forma 2: Keyword arguments  
            result2 = contract_generator_tool.invoke(
                employee_data=employee_data,
                it_credentials=it_credentials, 
                contractual_data=contractual_data,
                template_version="v2024.1"
            )
            print(f"✅ Keyword args: {result2.get('success', False)}")
        except Exception as e:
            print(f"❌ Keyword args failed: {e}")
            
        try:
            # Forma 3: Single dict (como IT Agent)
            input_dict = {
                "employee_data": employee_data,
                "it_credentials": it_credentials,
                "contractual_data": contractual_data,
                "template_version": "v2024.1"
            }
            result3 = contract_generator_tool.invoke(input_dict)
            print(f"✅ Single dict: {result3.get('success', False)}")
        except Exception as e:
            print(f"❌ Single dict failed: {e}")
            
        # Comparar con IT tool que funciona
        try:
            from agents.it_provisioning.tools import it_request_generator_tool
            it_result = it_request_generator_tool.invoke(
                employee_data=employee_data,
                equipment_specs={},
                priority="medium"
            )
            print(f"✅ IT tool works: {it_result.get('success', False)}")
        except Exception as e:
            print(f"❌ IT tool failed: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_simple_tools()