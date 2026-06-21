# 遺物管理工具使用方式

此工具依照 `docs/relic-workflow.md` 實作資料流程與 CLI 入口。

## 安裝依賴

```powershell
python -m pip install -r requirements.txt
```

## 建立設定檔

```powershell
python -m ern_relics_helper.cli init-config --output config/relic-helper.json
```

## 建立詞條對照表

可從完整來源 Excel 抽出標準格式詞條表：

```powershell
python -m ern_relics_helper.cli build-terms --source "【艾爾登法環：黑夜君臨】DLC全遺物、武器固有效果、護符、潛在能力、武器隨機buff（適配遊戲1.03.5）.xlsx" --output outputs/relic_terms_table/遺物詞條對照表.xlsx
```

標準詞條表欄位：

- `詞條`
- `詞條種類`
- `疊加`
- `邏輯判斷`
- `評分`

`邏輯判斷` 可填入 `特定武器`、`強力`、`不可疊加強力`、`不同級別可疊加強力`、`可疊加強力` 等標籤，多個標籤可用 `；` 分隔。

## 評估多餘遺物

輸入檔需包含 `unique_id`、`保留標記`、`遺物種類`、`詞條1` 到 `詞條6` 等欄位。

可先建立範本：

```powershell
python -m ern_relics_helper.cli create-relic-template --output outputs/scan/當前遺物清單.xlsx
```

```powershell
python -m ern_relics_helper.cli evaluate --relics outputs/scan/當前遺物清單.xlsx --terms outputs/relic_terms_table/遺物詞條對照表.xlsx --output-all outputs/evaluation/所有遺物狀態.xlsx --output-new outputs/evaluation/新增保留遺物.xlsx --threshold 0.5
```

輸出：

- `所有遺物狀態.xlsx`
- `新增保留遺物.xlsx`

## 移除檔案中的保留標記

```powershell
python -m ern_relics_helper.cli clear-marks-file --relics outputs/evaluation/所有遺物狀態.xlsx --output outputs/evaluation/移除保留標記後.xlsx
```

## 遊戲操作入口

以下命令已保留入口，但目前需要接入實際的畫面辨識與操作 adapter 後才會執行：

- `scan-game`
- `apply-keep`
- `delete-unkept`
- `clear-keeps-game`

這些入口目前會明確回報尚未接入 adapter，避免在未設定完成時操作遊戲。
