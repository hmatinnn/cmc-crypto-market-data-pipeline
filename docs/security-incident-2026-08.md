# Təhlükəsizlik düzəlişi — `config/airflow.cfg` sızması

**Tapan:** CI `Secret scan` job-u (gitleaks v8.30.1)
**Tarix:** 2026-08-06

---

## 1. Nə tapıldı

`config/airflow.cfg` faylı repoya commit olunmuşdu (commit `a5ecdd11`, 2026-07-08) və 3 real açar saxlayırdı:

| Sətir | Açar | Nə üçün istifadə olunur | Vəziyyət |
|---|---|---|---|
| 169 | `fernet_key` | Airflow Connections-dakı parolları şifrələyir | **İşlək deyildi** — `.env`-dəki `FERNET_KEY` onu override edirdi |
| 1332 | `secret_key` | Webserver sessiya cookie imzası | **İşlək idi** — env override yox idi |
| 1739 | `jwt_secret` | API JWT imzası | İşlək deyildi — compose `${AIRFLOW__API_AUTH__JWT_SECRET:-...}` override edir |

Fayl 4161 sətirlik idi, amma məzmunlu konfiqurasiya saxlamırdı — Airflow onu ilk işə düşəndə özü generasiya edir və bütün 12 vacib parametr `docker-compose.yaml`-dakı `AIRFLOW__*` env dəyişənlərindən gəlir.

---

## 2. Nə edilib (avtomatik)

- `config/airflow.cfg` `.gitignore`-a əlavə olundu
- `config/.gitkeep` yaradıldı — volume mount (`./config:/opt/airflow/config`) üçün qovluq qalmalıdır
- **Hər üç açar lokal faylda yeniləndi** — sızan dəyərlər artıq heç bir yerdə işləmir

> Bu, düzəlişin **ən vacib hissəsidir**. Tarixçəni təmizləmək sızan dəyəri GitHub-ın keşindən dərhal silmir, amma açar rotasiya olunubsa, sızan dəyər onsuz da dəyərsizdir.

---

## 3. Sənin icra etməli olduqların

### Addım 0 — Backup (mütləq)

Qovluğu `Copy-Item` ilə kopyalamağa **çalışma** — `logs/dag_processor/latest` Airflow-un
konteyner içində yaratdığı Linux symlink-idir və Windows ona ilişir
(`The file cannot be accessed by the system`).

Bizə lazım olan onsuz da git tarixçəsidir, ona görə `git bundle` daha düzgündür:

```powershell
git bundle create ..\cmc-repo-backup.bundle --all
```
```powershell
git bundle verify ..\cmc-repo-backup.bundle
```

Bu bir fayla bütün branch və commit-ləri yığır. Bərpa lazım olsa:

```powershell
git clone ..\cmc-repo-backup.bundle restored-repo
```

### Addım 1 — Faylı izlənmədən çıxar və commit et

```powershell
git rm --cached config/airflow.cfg
```
```powershell
git add .gitignore config/.gitkeep
```
```powershell
git commit -m "security: stop tracking config/airflow.cfg (contains generated secrets)"
```

### Addım 2 — Airflow-u yenidən başlat (yeni açarlar üçün)

```powershell
docker compose restart airflow-apiserver airflow-scheduler
```

Airflow UI-dan çıxmış olacaqsan — yenidən login et. Bu gözləniləndir, `secret_key` dəyişdi.

### Addım 3 — `git filter-repo` quraşdır

```powershell
pip install git-filter-repo
```

### Addım 4 — Faylı BÜTÜN tarixçədən sil

```powershell
git filter-repo --path config/airflow.cfg --invert-paths --force
```

Bu əmr `dev` və `main` daxil olmaqla bütün branch-ləri yenidən yazır. Commit SHA-ları dəyişir.

### Addım 5 — Remote-u geri qaytar

`git filter-repo` təhlükəsizlik üçün `origin`-i silir:

```powershell
git remote add origin https://github.com/hmatinnn/cmc-crypto-market-data-pipeline.git
```

### Addım 6 — Force push

```powershell
git push origin --force --all
```

### Addım 7 — Yoxla

```powershell
git log --all --oneline -- config/airflow.cfg
```

Boş qayıtmalıdır. Sonra GitHub-da Actions → yeni run → `Secret scan` yaşıl olmalıdır.

---

## 4. Diqqət ediləcək məqamlar

**PR #3 (`dev → main`)** — force-push-dan sonra PR yenilənəcək. Qəribə görünsə, bağlayıb yenidən aç.

**GitHub keşi** — force-push-dan sonra köhnə commit-lər bir müddət birbaşa SHA linki ilə əlçatan qala bilər (`.../commit/a5ecdd11`). GitHub onları öz vaxtında təmizləyir. Repo-nu public etməzdən əvvəl tam əminlik istəyirsənsə, GitHub Support-dan keşin təmizlənməsini xahiş et. **Açarlar rotasiya olunduğu üçün praktiki risk yoxdur.**

**Əgər tarixçə təmizləmə alınmasa** və CI-ı müvəqqəti keçirmək lazım olsa, `.gitleaks.toml`-a bu bloku əlavə et:

```toml
[allowlist]
# MÜVƏQQƏTİ - tarixçə təmizlənən kimi silinməlidir
commits = ["a5ecdd114d01f17f7ebd80f6c8dfc8317f4db226"]
```

Bu, problemi həll etmir, sadəcə gizlədir — uzun müddət saxlama.

---

## 5. Gələcəkdə təkrarlanmaması üçün

CI-dakı `Secret scan` job-u artıq hər push və PR-da bütün git tarixçəsini yoxlayır. Eyni səhv bir daha `main`-ə çata bilməz.

Lokal olaraq push-dan əvvəl yoxlamaq istəsən:

```powershell
gitleaks git . --config .gitleaks.toml --redact
```
