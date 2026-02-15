import zipfile
import os

mxl_folder = "D:/AI-Stuff/NotaGen/data/einaudi/mxl"
xml_output_folder = "D:/AI-Stuff/NotaGen/data/einaudi/xml"

os.makedirs(xml_output_folder, exist_ok=True)

for file in os.listdir(mxl_folder):
    if file.endswith(".mxl"):
        file_path = os.path.join(mxl_folder, file)
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                extracted = False
                for zip_file in zip_ref.namelist():
                    if zip_file.endswith(".xml"):
                        extracted_file_path = os.path.join(xml_output_folder, os.path.basename(file).replace(".mxl", ".xml"))
                        with open(extracted_file_path, "wb") as f:
                            f.write(zip_ref.read(zip_file))
                        print(f"✅ Extracted {zip_file} -> {extracted_file_path}")
                        extracted = True
                if not extracted:
                    print(f"❌ No XML file found in {file}")
        except zipfile.BadZipFile:
            print(f"⚠️ Error: {file} is not a valid zip file")
