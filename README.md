# ふたりのおまじない

仮素材で動作する、スマホ優先のZINE紹介サイト。決済・会員登録・送信機能はありません。

## 開発
Node.js 22以上。`npm ci --cache /workspace/.npm-cache` の後、`npm run dev`。
`npm run build` で静的サイトを `dist/` に出力します。配信するのは **dist/ のみ**です。
`npm run preview` でビルド結果を確認できます。

## 商品・カード・背景の差し替え
`config.js` が商品情報・カード・背景の設定場所です。
- `product.price`: 現在500円。`priceNote`も変更可能。
- `product.dmUrl`: 正式なHTTPSのDMリンクが届いたときだけ指定。未設定時はリンクを表示しません。
- `cards`: 画像・名前・idを追加して10枚まで運用可能。完成素材は `provisional:false` にします。
- `backgrounds`: 自作または利用許可のある写真を `public/assets/` に置き指定します。
- `hand.image`: 自作の仮の手イラスト。使用許可済みの透過素材へ差し替え可能。カードとの合成位置は `src.js` の `draw()` 内で調整できます。
- 表紙などの仮SVGは仮素材と明示。本文は未作成で、見本の罫線のみです。架空の本文は掲載していません。

## 本物のPDFで試し読みを作る
完全版PDFを **`private/book.pdf`** に置きます。`private/` はGit対象外、Viteの公開ディレクトリ外です。開発サーバーにも private/ とPDFファイルの配信拒否を設定しています。完全版を `public/` に置かないでください。

1. `python3 -m venv /workspace/zine-tools` を作り、`/workspace/zine-tools/bin/pip install PyMuPDF==1.26.7`。
2. `scripts/sample-selection.json` の `spreads` に公開する **PDFページ番号（1始まり）** を表示順で指定。例 `[2,4]` は2–3と6–7です。並べ替え・追加もここだけで行えます。
3. リポジトリ直下で `/workspace/zine-tools/bin/python scripts/export_sample.py` を実行。
4. 16–1の右半分を表紙、左半分を裏表紙として自動分割。選択した本文だけにSAMPLEを焼き込み、画像とmanifestを `public/assets/sample/` に作ります。省略箇所には区切りが入ります。未選択ページと元PDFは出力しません。
5. サイトはmanifestを自動検出。表示・拡大を確認してから再ビルドしてください。画像は保存可能なので、公開してよい抜粋のみ指定してください。

`booklet.cover` で表紙を指定できます。PDFを抜粋した場合は生成された表紙をヒーロー・サイズ比較にも自動反映します。`hand.provisional`、`booklet.provisional` も完成時に false にします。最初に仮素材一式を完成素材に替えたら、`src.js` 内の仮素材説明も確認してください。PDF由来本文の透かしは画像に焼き込み済みで、CSSを外しても残ります。

## 画像保存
Canvas上のドラッグ、位置・大きさ・角度スライダーで調整。900×1600 PNGで端末に保存します。アップロード写真はブラウザ内でのみ処理し、サーバーへ送りません。背景・カードは同じサイト内の画像を指定してください。外部URLはCanvas書き出し制限を受ける場合があります。仮の手素材は自作SVGで、完成写真の手とは明確に区別しています。

## 検証
`npm run dev` を起動した状態で `npx playwright test`。この環境では `/usr/bin/chromium` を使用します。スマホ・PCの横はみ出し、試し読み・拡大・カード・画像保存・JSエラーを確認します。
