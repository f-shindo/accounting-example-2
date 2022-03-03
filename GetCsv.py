import requests
import json
import pandas as pd
import settings


def make_df(address):
    # ERC20のやり取りを見たいアドレスとEtherscanのAPI KEYを入力しましょう
    api_key = settings.ETH

    # 実際にEtherscanのAPIに対してリクエストを行うURLを作成
    url = f'https://api.etherscan.io/api?module=account&action=tokentx&address={address}&startblock=0&endblock=99999999&offset=1000&sort=asc&apikey={api_key}'

    # 実際にEtherscanからAPIを用いてデータを取得
    response = requests.get(url)

    # 取得したデータのうち必要なデータを取得
    txs = json.loads(response.text)
    df = pd.DataFrame(txs['result'])

    # 最終的に出力するためのデータフレームを準備
    df_fin = pd.DataFrame(index=df.index, columns=[])

    # timeStampを日時(日本時間)に変換
    df_fin['JST'] = pd.to_datetime(
        df['timeStamp'].astype(int) + 60*60*9, unit='s')

    # valueを小数点を考慮した値に変換してdf_finに格納
    df_fin['fixed_value'] = df['value'].astype(
        'float128')/pow(10, df['tokenDecimal'].astype('float128'))
    df_fin.head()

    # 送信、受信の判定(inとoutの列を追加し、その列にvalueの値を入れる)
    df_fin['in'] = 0  # df_finにinという列を追加し、全て0を格納
    df_fin['out'] = 0  # df_finにoutという列を追加し、全て0を格納
    # 自分のウォレットのアドレスがあったらTRUEを返す関数を定義
    def func_my_wallet(x): return x in address.lower()
    tmp_in = df['to'].apply(func_my_wallet)  # dfのある列にfunc_my_wallet関数を適用
    df_fin.loc[tmp_in,  'in'] = df_fin.loc[tmp_in,  'fixed_value']
    tmp_out = df['from'].apply(func_my_wallet)  # dfのある列にfunc_my_wallet関数を適用
    df_fin.loc[tmp_out,  'out'] = df_fin.loc[tmp_out,  'fixed_value']

    # 使用したgas代を計算(自分が消費したgasと等価ではないので注意しましょう)
    df_fin['gas'] = df['gasPrice'].astype(
        'float128') * df['gasUsed'].astype('float128') / pow(10, 18)

    # その他残しておきたい情報をdf_finに格納
    df_fin[['hash', 'from', 'to', 'tokenName', 'tokenSymbol', 'contractAddress']] = df[[
        'hash', 'from', 'to', 'tokenName', 'tokenSymbol', 'contractAddress']]

    df_fin['price'] = float(0)

    # contractアドレスを全ての行から取得しておく
    contract_address_list = df['contractAddress']

    # timeStampをcoingeckoのAPIの書式に合わせた日時の形式に変換しておく
    def func_to_date(x): return x.strftime('%d-%m-%Y')
    date_list = pd.to_datetime(df['timeStamp'].astype(
        int), unit='s').apply(func_to_date)

    for i, (contract_address, date) in enumerate(zip(contract_address_list, date_list)):
        #　coingecko APIに問い合わせてcoin idを取得する
        response = requests.get(
            f'https://api.coingecko.com/api/v3/coins/ethereum/contract/{contract_address}')
        if response.ok:
            token_id = json.loads(response.text)['id']
        # responseがokでない場合には次のforループに移動する　※responseの内容に合わせて条件分岐を細かくした方が良いですが、今回は省略しています
        else:
            continue
        #　coin idと日時のデータを元にcoingecko APIに問い合わせて価格データを取得する
        response = requests.get(
            f'https://api.coingecko.com/api/v3/coins/{token_id}/history?date={date}')
        if response.ok:
            df_fin['price'][i] = json.loads(response.text)[
                'market_data']['current_price']['jpy']
        # responseがokでない場合には次のforループに移動する　※responseの内容に合わせて条件分岐を細かくした方が良いですが、今回は省略しています
        else:
            continue
    return df_fin
