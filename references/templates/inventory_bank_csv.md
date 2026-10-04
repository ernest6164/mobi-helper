# 템플릿: 인벤토리 및 보관함 재고 CSV (`characters/*.csv`)

* **대상 파일**:
  * 인벤토리: `data/characters/(서버명)_(캐릭터명)_inventory.csv`
  * 개인 보관함: `data/characters/(서버명)_(캐릭터명)_bank.csv`
  * 공용 보관함: `data/characters/(서버명)_bank_all.csv`
* **설명**: 인벤토리, 개인 금고, 서버 공용 금고의 아이템 목록을 관리하는 테이블 데이터입니다.

---

```csv
Location,DisplayName,Category,CategoryDisplayName,Count,IsLocked
inventory,정령의 날개,Currency,재화,53357,False
inventory,룬의 파편,Ingredient,재료,3733,False
inventory,연금술 부스러기,Ingredient,재료,44658,False
inventory,얼음,Ingredient,재료,22,False
inventory,황금 양털,Ingredient,재료,1,True
```
