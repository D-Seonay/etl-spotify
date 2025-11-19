"""
Script de test pour l'endpoint d'import via l'API FastAPI.

Ce script teste l'import via l'endpoint /api/v1/import-data
avec enrichissement Spotify.
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()


def test_api_import():
    """Teste l'import via l'API FastAPI."""
    print("\n" + "="*60)
    print("🧪 Test de l'endpoint d'import API")
    print("="*60 + "\n")
    
    # Configuration
    api_url = "http://127.0.0.1:8000"
    api_key = os.getenv('API_KEY')
    test_file = "data/Streaming_History_Audio_2021-2024_0.json"
    
    # Vérifier que le fichier existe
    if not os.path.exists(test_file):
        print(f"❌ Fichier {test_file} non trouvé")
        print("   Modifiez la variable 'test_file' dans ce script")
        return False
    
    # Vérifier la clé API
    if not api_key or api_key == 'your_api_key_here':
        print("❌ API_KEY non configurée dans .env")
        return False
    
    print(f"📁 Fichier à importer: {test_file}")
    print(f"🔑 API Key: {api_key[:20]}...\n")
    
    # Vérifier que l'API est accessible
    print("1️⃣  Vérification de l'API...")
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API accessible\n")
        else:
            print(f"❌ API non accessible (status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API non accessible")
        print("   Lancez l'API avec: uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Préparer la requête
    print("2️⃣  Envoi du fichier à l'endpoint d'import...")
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    with open(test_file, 'rb') as f:
        files = {
            'file': (os.path.basename(test_file), f, 'application/json')
        }
        
        data = {
            'user_id': 'test_user'
        }
        
        try:
            response = requests.post(
                f"{api_url}/api/v1/import-data",
                headers=headers,
                files=files,
                data=data,
                timeout=300  # 5 minutes pour l'enrichissement
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Import réussi!\n")
                
                print("📊 Résultats:")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}\n")
                
                stats = result['statistics']
                print("📈 Statistiques:")
                print(f"   Artistes importés: {stats['artists_imported']}")
                print(f"   Albums importés: {stats['albums_imported']}")
                print(f"   Tracks importées: {stats['tracks_imported']}")
                print(f"   Écoutes importées: {stats['history_entries_imported']}")
                
                print("\n" + "="*60)
                print("✨ Test réussi!")
                print("="*60 + "\n")
                return True
            
            else:
                print(f"❌ Erreur HTTP {response.status_code}")
                print(f"   {response.text}")
                return False
        
        except requests.exceptions.Timeout:
            print("⏱️  Timeout - L'enrichissement peut prendre du temps")
            print("   Vérifiez les logs de l'API pour voir la progression")
            return False
        
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False


def test_api_import_multiple():
    """Teste l'import de plusieurs fichiers via l'API."""
    print("\n" + "="*60)
    print("🧪 Test de l'endpoint d'import multiple")
    print("="*60 + "\n")
    
    # Configuration
    api_url = "http://127.0.0.1:8000"
    api_key = os.getenv('API_KEY')
    test_files = [
        "data/Streaming_History_Audio_2021-2024_0.json",
        "data/Streaming_History_Audio_2024-2025_1.json"
    ]
    
    # Vérifier que les fichiers existent
    existing_files = [f for f in test_files if os.path.exists(f)]
    if not existing_files:
        print(f"❌ Aucun fichier trouvé")
        print("   Modifiez la variable 'test_files' dans ce script")
        return False
    
    print(f"📁 {len(existing_files)} fichiers à importer:")
    for f in existing_files:
        print(f"   - {f}")
    print()
    
    # Vérifier que l'API est accessible
    print("1️⃣  Vérification de l'API...")
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ API accessible\n")
        else:
            print(f"❌ API non accessible (status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API non accessible")
        print("   Lancez l'API avec: uvicorn main:app --reload")
        return False
    
    # Préparer la requête
    print("2️⃣  Envoi des fichiers à l'endpoint d'import...")
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    files_data = []
    for file_path in existing_files:
        files_data.append(
            ('files', (os.path.basename(file_path), open(file_path, 'rb'), 'application/json'))
        )
    
    data = {
        'user_id': 'test_user'
    }
    
    try:
        response = requests.post(
            f"{api_url}/api/v1/import-multiple",
            headers=headers,
            files=files_data,
            data=data,
            timeout=600  # 10 minutes pour plusieurs fichiers
        )
        
        # Fermer les fichiers
        for _, (_, f, _) in files_data:
            f.close()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Import réussi!\n")
            
            print("📊 Résultats:")
            print(f"   Status: {result['status']}")
            print(f"   Message: {result['message']}")
            print(f"   Fichiers importés: {', '.join(result['imported_files'])}")
            if result.get('errors'):
                print(f"   Erreurs: {result['errors']}\n")
            else:
                print()
            
            stats = result['total_statistics']
            print("📈 Statistiques totales:")
            print(f"   Artistes importés: {stats['artists_imported']}")
            print(f"   Albums importés: {stats['albums_imported']}")
            print(f"   Tracks importées: {stats['tracks_imported']}")
            print(f"   Écoutes importées: {stats['history_entries_imported']}")
            
            print("\n" + "="*60)
            print("✨ Test réussi!")
            print("="*60 + "\n")
            return True
        
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"   {response.text}")
            return False
    
    except requests.exceptions.Timeout:
        print("⏱️  Timeout - L'enrichissement peut prendre du temps")
        print("   Vérifiez les logs de l'API pour voir la progression")
        return False
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


if __name__ == "__main__":
    import sys
    
    print("\n🎵 Tests de l'API d'import Spotify")
    print("\n⚠️  Assurez-vous que:")
    print("   1. L'API est lancée: uvicorn main:app --reload")
    print("   2. Les credentials Spotify sont configurés dans .env")
    print("   3. La base de données est accessible\n")
    
    input("Appuyez sur Entrée pour continuer...")
    
    # Test simple
    success1 = test_api_import()
    
    if success1:
        print("\n" + "─"*60 + "\n")
        
        # Test multiple
        response = input("Voulez-vous tester l'import multiple ? (o/N): ")
        if response.lower() == 'o':
            success2 = test_api_import_multiple()
            sys.exit(0 if success1 and success2 else 1)
    
    sys.exit(0 if success1 else 1)
