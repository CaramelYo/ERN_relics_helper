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

## 設定遊戲視窗與區域

列出目前可見視窗，找出遊戲視窗標題：

```powershell
python -m ern_relics_helper.cli list-windows
```

編輯 `config/relic-helper.json`：

- `game.window_title`：遊戲視窗標題的一部分。
- `ocr.tesseract_cmd`：Tesseract 執行檔路徑，例如 `C:\Program Files\Tesseract-OCR\tesseract.exe`。
- `ocr.language`：OCR 語言，繁中建議 `chi_tra+eng`。
- `scan.max_relics`：最多瀏覽幾個遺物，必須大於 `0`。
- `regions.relic_kind`：遺物種類區域。
- `regions.relic_terms`：遺物詞條區域。
- `regions.keep_marker`：保留標記偵測區域。

區域格式皆為相對遊戲視窗左上角的座標：

```json
{"x": 100, "y": 200, "width": 300, "height": 120}
```

可用以下命令截圖檢查區域是否正確：

```powershell
python -m ern_relics_helper.cli capture-region --config config/relic-helper.json --region relic_terms --output outputs/debug/relic_terms.png
```

## 設定遊戲操作

`actions.move_next`、`actions.toggle_keep`、`actions.delete_relic` 都是動作序列。

鍵盤範例：

```json
[
  {"type": "key", "key": "RIGHT"},
  {"type": "wait", "seconds": 0.1}
]
```

滑鼠範例：

```json
[
  {"type": "click", "x": 1200, "y": 720}
]
```

`x`、`y` 是相對遊戲視窗左上角的位置。

支援常見按鍵：`UP`、`DOWN`、`LEFT`、`RIGHT`、`ENTER`、`ESC`、`SPACE`、`TAB`、`DELETE`、`F1` 到 `F24`，以及單一英文字母或數字。

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

以下命令會使用設定檔中的視窗、區域、OCR 與操作設定：

```powershell
python -m ern_relics_helper.cli scan-game --config config/relic-helper.json --terms outputs/relic_terms_table/遺物詞條對照表.xlsx --output outputs/scan/當前遺物清單.xlsx
```

保留特定遺物：

```powershell
python -m ern_relics_helper.cli apply-keep --config config/relic-helper.json --terms outputs/relic_terms_table/遺物詞條對照表.xlsx --input outputs/evaluation/新增保留遺物.xlsx --execute
```

刪除未保留遺物：

```powershell
python -m ern_relics_helper.cli delete-unkept --config config/relic-helper.json --terms outputs/relic_terms_table/遺物詞條對照表.xlsx --execute
```

移除所有保留標記：

```powershell
python -m ern_relics_helper.cli clear-keeps-game --config config/relic-helper.json --terms outputs/relic_terms_table/遺物詞條對照表.xlsx --execute
```

`apply-keep`、`delete-unkept`、`clear-keeps-game` 若未加 `--execute`，會執行掃描與比對，但不會送出保留、刪除或移除標記按鍵。

## 保留標記偵測

若要偵測保留標記，需設定：

```json
{
  "marker_detection": {
    "enabled": true,
    "rgb": [255, 255, 255],
    "tolerance": 32,
    "minimum_ratio": 0.02
  }
}
```

程式會在 `regions.keep_marker` 中統計接近 `rgb` 的像素比例，高於 `minimum_ratio` 即視為有保留標記。
