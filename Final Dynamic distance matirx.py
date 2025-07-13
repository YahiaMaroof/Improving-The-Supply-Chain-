import googlemaps
import pandas as pd

# 🔐 أدخل مفتاح Google Maps API الخاص بك هنا
API_KEY = "AIzaSyBmOW3KV_OtHWWstqDRPQBUVUCXP4E9Ua8"
gmaps = googlemaps.Client(key=API_KEY)

# 🏷️ أسماء الموردين
supplier_names = [
     "المخزن",
     "الوكاله للسيارات",
     "رواسي",
     "نجم الرمال",
     "الغفيلي",
     "الشرق",
     "ركن الراقي",
     "توكيلات الجزيره",
     "المهري",
     "بيت التزامن",
     "الوان العربه",
     "ساماكو",
     "تشليح الحائر",
     "الحاج حسين",
     "المغلوث",
     "اهل الخبرة",
     "اوتوبانوراما",
     "شمس الاصناف",
     "ضياء البشائر",
     "مصدر الزيوت",
     "الإطار الكبير",
     "الوعلان",
     "رينيو(وكيل رينيو السابق)",
     "امبوبه",
     "العمودي",
     "منيف النهدي",
     "منيف النهدي",
     "القحطاني",
     "الناغي",
     "نجمة نيسان"
]

# 📍 الإحداثيات المقابلة للأسماء
supplier_locations = [
 "24.647411671633186, 46.733357823156254",
 "24.845732140510165, 46.83772791388598",
 "24.71497611459734, 46.85154226441841",
 "24.63525338912695, 46.75119129325291",
 "24.638851840518754, 46.75381729726751",
 "24.640334226653497, 46.73701425831106",
 "24.63763632960209, 46.69798201413471",
 "24.639905494636505, 46.73870507180525",
 "24.588637127160855, 46.741808973652155",
 "24.639102492055553, 46.74293732393508",
 "24.637583781783757, 46.73997505092344",
 "24.75728130813972, 46.83698455359912",
 "24.530028461748053, 46.796529139290044",
 "24.71097985325633, 46.76433549578683",
 "24.639066392114753, 46.74375391541574",
 "24.63080492161978, 46.80019008473356",
 "24.633886795771236, 46.74362784851069",
 "24.632542240204977, 46.7439049387103",
 "24.63077313179229, 46.743776101921554",
 "24.79685957045473, 46.87668998286495",
 "24.630906868750436, 46.739725062004865",
 "24.755653000336398, 46.681146804334325",
 "24.643137492893977, 46.74280038085473",
 "24.692337824277736, 46.85420735771145",
 "24.63060854261958, 46.742010002487426",
 "24.635681945385517, 46.74341183459995",
 "24.58540762379448, 46.686121521522324",
 "24.77369655611179, 46.67640812152232",
 "24.630372368751107, 46.74131737734596",
 "24.63726862141617, 46.738920898227754"

]

# 🏗️ تهيئة DataFrame فارغ بأسماء الموردين
distance_matrix = pd.DataFrame(index=supplier_names, columns=supplier_names)

# 🔁 إرسال طلبات لكل زوج من المواقع بشكل مجزأ لتجنب تجاوز حدود واجهة برمجة التطبيقات
chunk_size = 10  # حجم كل جزء (10x10 = 100 عنصر، وهو الحد الأقصى)

for i in range(0, len(supplier_locations), chunk_size):
    origins_chunk = supplier_locations[i:i + chunk_size]
    
    for j in range(0, len(supplier_locations), chunk_size):
        destinations_chunk = supplier_locations[j:j + chunk_size]
        
        result = gmaps.distance_matrix(origins=origins_chunk,
                                       destinations=destinations_chunk,
                                       mode='driving')
        
        for k, row in enumerate(result['rows']):
            origin_index = i + k
            for l, element in enumerate(row['elements']):
                destination_index = j + l
                try:
                    distance_meters = element['distance']['value']
                    distance_km = round(distance_meters / 1000, 2)
                    distance_matrix.iloc[origin_index, destination_index] = distance_km
                except (KeyError, IndexError):
                    distance_matrix.iloc[origin_index, destination_index] = None

# �� حفظ النتيجة في ملف Excel
output_path = r"E:\distances.xlsx"
distance_matrix.to_excel(output_path, encoding="utf-8-sig")
print(distance_matrix)
print(f"File saved to: {output_path}")

