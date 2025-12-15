# 🎯 Proje Yönetim Sistemi - Detaylı Türkçe Kılavuz

## 📖 Sistem Nasıl Çalışıyor?

### Temel Mantık

Bu sistem, **her yeni Cursor chat açtığınızda AI'ın projenin tam durumunu otomatik olarak anlamasını** sağlar. Normalde her chat'te AI'a uzun uzun açıklama yapmanız gerekir, ama bu sistem sayesinde AI zaten her şeyi biliyor!

### Nasıl Yapıldı?

1. **Mevcut Durumu Analiz Ettim**
   - `STATUS-CHECK.md` dosyasını okudum (ne yapılmış, ne test edilmiş)
   - Kod tabanını inceledim (backend/frontend yapısı)
   - Dokümantasyonu gözden geçirdim (PRD, roadmap, vb.)

2. **4 Ana Dosya Oluşturdum**
   - `CURSOR-PROJECT-MANAGER.md` - Ana bağlam dosyası (AI'ın "beyni")
   - `PROJECT-STATUS.md` - Anlık durum takibi
   - `QUICK-ACTIONS.md` - Hızlı komut referansı
   - `.cursor/rules/project-management.md` - Cursor kuralları

3. **Her Dosyanın Rolü**
   - **CURSOR-PROJECT-MANAGER.md**: AI'ın her chat'te okuduğu ana dosya. Projenin tam durumu burada.
   - **PROJECT-STATUS.md**: Her oturum sonrası güncellenen, "ne yapıldı, ne kaldı" bilgisi.
   - **QUICK-ACTIONS.md**: İki kelimelik komutların listesi ve anlamları.
   - **project-management.md**: AI'a "bu dosyaları nasıl kullanacağını" söyleyen kural dosyası.

---

## 🔄 Sistemin Çalışma Mantığı

### Senaryo 1: Yeni Chat Açıyorsunuz

```
1. Cursor Chat'i açıyorsunuz (Cmd/Ctrl + L)
2. AI otomatik olarak şunları yapıyor:
   - .cursor/rules/project-management.md'yi okuyor
   - "Her chat'te CURSOR-PROJECT-MANAGER.md'yi oku" kuralını görüyor
   - CURSOR-PROJECT-MANAGER.md'yi okuyor
   - Projenin tam durumunu öğreniyor:
     * Ne yapılmış? ✅
     * Ne test edilmiş? 🧪
     * Ne kaldı? 🚧
     * Öncelikli görevler neler? 🎯
3. Artık AI her şeyi biliyor!
```

### Senaryo 2: Hızlı Komut Kullanıyorsunuz

```
Siz: "implement comfyui manager"

AI'nın Yaptıkları:
1. QUICK-ACTIONS.md'yi kontrol ediyor
   → "implement comfyui manager" = "ComfyUI yönetim sayfası oluştur"
   
2. CURSOR-PROJECT-MANAGER.md'yi okuyor
   → "Recommended Next Tasks" bölümünde bunu görüyor
   → Detayları anlıyor:
     * ComfyUI indirme
     * Başlatma/durdurma
     * Log görüntüleme
     * Durum izleme
   
3. STATUS-CHECK.md'yi kontrol ediyor
   → ComfyUI ile ilgili ne var?
   → `/api/comfyui/status` endpoint'i var
   → Ama UI yok, onu yapmalı
   
4. Kodu yazıyor:
   - Backend: Gerekirse yeni endpoint'ler
   - Frontend: /comfyui sayfası oluşturuyor
   - Tüm özellikleri ekliyor
   
5. PROJECT-STATUS.md'yi güncelliyor
   → "ComfyUI manager completed" yazıyor
```

### Senaryo 3: Durum Sorguluyorsunuz

```
Siz: "show what's left"

AI'nın Yaptıkları:
1. CURSOR-PROJECT-MANAGER.md'yi okuyor
2. "What Remains" bölümünü buluyor
3. Size özet sunuyor:
   - A) ComfyUI Bundle & Launch
   - B) Image Workflows
   - C) Video Pipeline
   - D) Platform Integration
```

---

## 📁 Dosyaların Detaylı Açıklaması

### 1. CURSOR-PROJECT-MANAGER.md (Ana Dosya)

**Bu dosya ne yapıyor?**
- AI'ın "hafızası" gibi çalışıyor
- Her chat'te AI bu dosyayı okuyor
- Projenin tam durumunu içeriyor

**İçinde ne var?**
```
✅ What's Built & Shipped
   → Backend API'ler (installer, models, comfyui, generate, content)
   → Frontend sayfaları (/installer, /models, /generate)
   → Her özelliğin detaylı listesi

🧪 What's Tested & Verified
   → Ne test edilmiş?
   → Ne end-to-end doğrulanmış?
   → Ne sadece kod seviyesinde?

🚧 What Remains
   → Kalan görevler
   → Öncelik sırasına göre
   → Detaylı checklist'ler

🎯 Recommended Next Tasks
   → En yüksek etkili görevler
   → Neden öncelikli?
   → Nasıl yapılacak?
```

**Nasıl kullanılır?**
- AI otomatik okuyor (siz bir şey yapmıyorsunuz)
- İsterseniz manuel referans verebilirsiniz: "CURSOR-PROJECT-MANAGER.md'deki 'What Remains' bölümünü oku"

### 2. PROJECT-STATUS.md (Anlık Durum)

**Bu dosya ne yapıyor?**
- Her oturum sonrası güncelleniyor
- "Son yaptıklarımız neydi?" sorusuna cevap veriyor
- Hızlı durum kontrolü için

**İçinde ne var?**
```
✅ Recently Completed
   → Bu oturumda ne yapıldı?
   → Hangi özellikler tamamlandı?

🚧 Currently In Progress
   → Şu anda ne üzerinde çalışıyoruz?
   → Yarım kalan işler var mı?

🎯 Next Priority Tasks
   → Sıradaki görevler
   → Öncelik sırası

🧪 Testing Status
   → Ne test edildi?
   → Ne test bekliyor?
```

**Nasıl kullanılır?**
- Yeni chat açtığınızda: "show project status"
- AI bu dosyayı okuyup özet veriyor

### 3. QUICK-ACTIONS.md (Hızlı Komutlar)

**Bu dosya ne yapıyor?**
- İki kelimelik komutların listesi
- Her komutun ne yaptığını açıklıyor
- Kategorilere ayrılmış (öncelik, tip)

**İçinde ne var?**
```
🚀 Quick Commands (Tablo)
   Command                    | What It Does
   ---------------------------|----------------------------
   implement comfyui manager  | ComfyUI yönetim sayfası oluştur
   wire model sync            | Model Manager'ı ComfyUI'ye bağla
   add workflow presets      | Workflow preset sistemi ekle
   
📋 Usage Examples
   → Her komutun örnek kullanımı
   → AI'ın nasıl tepki vereceği

🎯 Command Categories
   → High Priority (öncelikli)
   → Medium Priority (orta)
   → Lower Priority (düşük)
```

**Nasıl kullanılır?**
- Sadece komutu yazın: "implement comfyui manager"
- AI QUICK-ACTIONS.md'yi okuyup ne yapacağını anlıyor
- Sonra CURSOR-PROJECT-MANAGER.md'den detayları alıyor
- Tam implementasyonu yapıyor

### 4. .cursor/rules/project-management.md (Kurallar)

**Bu dosya ne yapıyor?**
- AI'a "bu dosyaları nasıl kullanacağını" söylüyor
- Otomatik güncelleme kuralları
- Dosya ilişkileri

**İçinde ne var?**
```
📋 Project State Management
   → Hangi dosyayı ne zaman oku?
   → Görev tamamlandığında ne yap?

🔄 Update Frequency
   → PROJECT-STATUS.md: Her oturum sonrası
   → CURSOR-PROJECT-MANAGER.md: Büyük özellikler tamamlandığında
   → STATUS-CHECK.md: Doğrulama durumu değiştiğinde

💡 Best Practices
   → Her zaman bağlam önce
   → Görev tamamlandığında hemen güncelle
   → Test durumunu takip et
```

**Nasıl kullanılır?**
- AI otomatik okuyor
- Siz bir şey yapmıyorsunuz
- Ama AI bu kurallara göre davranıyor

---

## 🎮 Pratik Kullanım Senaryoları

### Senaryo 1: İlk Kez Kullanıyorsunuz

```
1. Cursor'ı açın
2. Chat'i açın (Cmd/Ctrl + L)
3. Yazın: "show project status"
4. AI size projenin durumunu özetler
5. Yazın: "show what's left"
6. AI size kalan görevleri listeler
7. Bir görev seçin: "implement comfyui manager"
8. AI tam implementasyonu yapar!
```

### Senaryo 2: Devam Eden Bir Özellik Var

```
1. Chat'i açın
2. Yazın: "show project status"
3. AI "Currently In Progress" bölümünü gösterir
4. Yazın: "continue working on [özellik adı]"
5. AI kaldığı yerden devam eder
```

### Senaryo 3: Yeni Bir Özellik Eklemek İstiyorsunuz

```
1. Chat'i açın
2. Yazın: "show what's built"
3. AI mevcut özellikleri listeler
4. Yazın: "add [yeni özellik]"
5. AI:
   - Önce kontrol eder (zaten var mı?)
   - Yoksa CURSOR-PROJECT-MANAGER.md'ye ekler
   - Implementasyonu yapar
   - PROJECT-STATUS.md'yi günceller
```

### Senaryo 4: Hızlı Komut Kullanımı

```
1. Chat'i açın
2. QUICK-ACTIONS.md'den bir komut seçin
3. Yazın: "implement comfyui manager"
4. AI:
   - QUICK-ACTIONS.md'yi okur (komutun anlamını öğrenir)
   - CURSOR-PROJECT-MANAGER.md'yi okur (detayları öğrenir)
   - STATUS-CHECK.md'yi kontrol eder (ne var, ne yok?)
   - Kodu yazar
   - Dosyaları günceller
```

---

## 💡 İleri Seviye Kullanım

### 1. Komutları Birleştirme

```
"implement comfyui manager and wire model sync"
→ AI iki görevi de yapar
```

### 2. Özel Bağlam Verme

```
"Based on CURSOR-PROJECT-MANAGER.md, implement ComfyUI manager 
but also add automatic model syncing"
→ AI hem ComfyUI manager'ı yapar hem de model sync ekler
```

### 3. Belirli Bölüm Referansı

```
"Read the 'What Remains' section from CURSOR-PROJECT-MANAGER.md 
and implement the first item"
→ AI sadece o bölümü okur ve ilk görevi yapar
```

### 4. Durum Güncelleme

```
"Update PROJECT-STATUS.md to mark ComfyUI manager as completed"
→ AI dosyayı günceller
```

---

## 🔍 Sistemin Avantajları

### 1. Hızlı Başlangıç
- Her chat'te uzun açıklama yapmaya gerek yok
- AI zaten projenin durumunu biliyor
- Direkt işe koyulabilirsiniz

### 2. İki Kelimelik Komutlar
- "implement comfyui manager" → Tam sayfa oluşturulur
- "wire model sync" → Model senkronizasyonu eklenir
- "add workflow presets" → Preset sistemi kurulur

### 3. Otomatik Takip
- AI görevleri tamamladığında dosyaları günceller
- Her oturum sonrası durum güncel kalır
- "Ne yaptık?" sorusuna otomatik cevap

### 4. Önceliklendirme
- En önemli görevler belirtilmiş
- "Ne yapmalıyım?" sorusuna net cevap
- Zaman kaybı yok

### 5. Bağlam Korunur
- Her chat önceki durumu bilir
- Yarım kalan işler takip edilir
- Süreklilik sağlanır

---

## 🛠️ Sistem Nasıl Güncellenir?

### Otomatik Güncelleme

AI görevleri tamamladığında:
1. `PROJECT-STATUS.md`'yi günceller
   - "Recently Completed" bölümüne ekler
   - "Currently In Progress" bölümünü temizler

2. `CURSOR-PROJECT-MANAGER.md`'yi günceller (büyük özellikler için)
   - "What's Built" bölümüne ekler
   - "What Remains" bölümünden çıkarır

3. `STATUS-CHECK.md`'yi günceller (doğrulama için)
   - Test durumunu günceller
   - Doğrulanmış özellikleri işaretler

### Manuel Güncelleme

Eğer AI güncellemezse:
```
"Update PROJECT-STATUS.md with completed tasks"
→ AI dosyayı günceller
```

Veya siz manuel düzenleyebilirsiniz (markdown dosyaları, kolay düzenlenir).

---

## 📊 Dosya İlişkileri

```
CURSOR-PROJECT-MANAGER.md (Ana Bağlam)
    │
    ├──→ PROJECT-STATUS.md (Anlık Durum)
    │       └──→ Her oturum sonrası güncellenir
    │
    ├──→ QUICK-ACTIONS.md (Komut Referansı)
    │       └──→ Komutlar buradan alınır
    │
    └──→ STATUS-CHECK.md (Gerçek Durum)
            └──→ Kod tabanından doğrulanır

.cursor/rules/project-management.md
    └──→ AI'a "nasıl kullanacağını" söyler
```

**Akış:**
1. AI `.cursor/rules/project-management.md`'yi okur
2. "CURSOR-PROJECT-MANAGER.md'yi oku" kuralını görür
3. CURSOR-PROJECT-MANAGER.md'yi okur
4. Proje durumunu öğrenir
5. Kullanıcı komut verdiğinde QUICK-ACTIONS.md'yi kontrol eder
6. Görevi tamamlar
7. PROJECT-STATUS.md'yi günceller

---

## 🎓 Öğrenme Yolu

### Başlangıç (İlk 5 Dakika)
1. Chat'i açın
2. "show project status" yazın
3. AI'ın ne dediğini okuyun
4. "show what's left" yazın
5. Kalan görevleri görün

### Orta Seviye (İlk Hafta)
1. QUICK-ACTIONS.md'yi açın
2. Bir komut seçin
3. Chat'te deneyin
4. AI'ın nasıl çalıştığını görün
5. Farklı komutlar deneyin

### İleri Seviye (İlk Ay)
1. Komutları birleştirin
2. Özel bağlam verin
3. Dosyaları manuel düzenleyin
4. Yeni komutlar ekleyin
5. Sistemin nasıl çalıştığını tam anlayın

---

## 🆘 Sorun Giderme

### Problem: AI komutu anlamıyor
**Çözüm:**
- QUICK-ACTIONS.md'den tam komutu kopyalayın
- Veya daha açıklayıcı yazın: "Add a ComfyUI management page with download, start, stop, and logs"

### Problem: Dosyalar güncellenmiyor
**Çözüm:**
- Açıkça söyleyin: "Update PROJECT-STATUS.md with what we just completed"
- Veya manuel düzenleyin (markdown, kolay)

### Problem: AI proje durumunu bilmiyor
**Çözüm:**
- Dosyayı referans verin: "Read CURSOR-PROJECT-MANAGER.md and tell me what's built"
- Veya ilgili bölümü chat'e kopyalayın

### Problem: Hızlı komut yok
**Çözüm:**
- QUICK-ACTIONS.md'ye ekleyin
- Veya açıklayıcı komut kullanın

---

## ✅ Hızlı Başlangıç Checklist

- [ ] Cursor'ı açın
- [ ] Chat'i açın (Cmd/Ctrl + L)
- [ ] "show project status" yazın
- [ ] Durumu görün
- [ ] "show what's left" yazın
- [ ] Kalan görevleri görün
- [ ] Bir görev seçin
- [ ] QUICK-ACTIONS.md'den komut bulun
- [ ] Komutu yazın
- [ ] AI'ın çalışmasını izleyin!

---

## 🎉 Sonuç

Bu sistem sayesinde:
- ✅ Her chat'te uzun açıklama yapmaya gerek yok
- ✅ İki kelimelik komutlarla işler yapılır
- ✅ Proje durumu her zaman güncel
- ✅ Öncelikler net
- ✅ Süreklilik sağlanır

**Hazırsanız:** Chat'i açın ve "show project status" yazın! 🚀

---

*Bu kılavuz, sistemin nasıl çalıştığını ve nasıl kullanılacağını detaylı olarak açıklar. Sorularınız olursa chat'te sorabilirsiniz!*
