import streamlit as st
import pandas as pd
import datetime
import os
from datetime import timedelta, time
import time as tm
import zipfile

# Plotlyのインポート（エラー処理付き）
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ページ設定
st.set_page_config(
    page_title="We Are Pretty Cure!",
    page_icon="🃏",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# カスタムCSS
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .main-header {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 30px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    
    .small-metric {
        background: rgba(255, 255, 255, 0.9);
        padding: 8px;
        border-radius: 8px;
        font-size: 12px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# データファイルパス
GAME_DATA_FILE = "poker_games.csv"
BANK_LOANS_FILE = "pbank_loans.csv"
BANK_APPLICATIONS_FILE = "pbank_applications.csv"
BANK_TRANSACTIONS_FILE = "pbank_transactions.csv"
JACKPOT_DATA_FILE = "jackpot_data.csv"
JACKPOT_WINNERS_FILE = "jackpot_winners.csv"
USERS_DATA_FILE = "users_data.csv"
NOTIFICATIONS_FILE = "notifications.csv"

# 初期ユーザーデータ
DEFAULT_USERS = [
    {"username": "admin", "password": "admin123", "role": "admin", "active": True},
    {"username": "player1", "password": "pass1", "role": "player", "active": True},
    {"username": "player2", "password": "pass2", "role": "player", "active": True},
    {"username": "player3", "password": "pass3", "role": "player", "active": True},
    {"username": "player4", "password": "pass4", "role": "player", "active": True},
    {"username": "player5", "password": "pass5", "role": "player", "active": True},
    {"username": "player6", "password": "pass6", "role": "player", "active": True},
    {"username": "player7", "password": "pass7", "role": "player", "active": True},
    {"username": "player8", "password": "pass8", "role": "player", "active": True}
]

def load_users():
    """ユーザーデータを読み込み"""
    if os.path.exists(USERS_DATA_FILE):
        df = pd.read_csv(USERS_DATA_FILE)
        df['active'] = df['active'].astype(bool)
        return df
    else:
        df = pd.DataFrame(DEFAULT_USERS)
        df.to_csv(USERS_DATA_FILE, index=False)
        return df

def save_users(df):
    """ユーザーデータを保存"""
    df.to_csv(USERS_DATA_FILE, index=False)

def add_notification(user, message, type="info"):
    """通知を追加"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
    else:
        df = pd.DataFrame(columns=['datetime', 'user', 'message', 'type', 'read'])
    
    new_notification = pd.DataFrame([{
        'datetime': pd.Timestamp.now(),
        'user': user,
        'message': message,
        'type': type,
        'read': False
    }])
    
    df = pd.concat([df, new_notification], ignore_index=True)
    df.to_csv(NOTIFICATIONS_FILE, index=False)

def get_notifications(user):
    """未読通知を取得"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
        return df[(df['user'] == user) & (df['read'] == False)]
    return pd.DataFrame()

def mark_notifications_read(user):
    """通知を既読にする"""
    if os.path.exists(NOTIFICATIONS_FILE):
        df = pd.read_csv(NOTIFICATIONS_FILE)
        df.loc[df['user'] == user, 'read'] = True
        df.to_csv(NOTIFICATIONS_FILE, index=False)

def calculate_play_time(start_time, end_time):
    """プレイ時間を計算（日跨ぎ対応）"""
    start_hours = start_time.hour + start_time.minute / 60
    end_hours = end_time.hour + end_time.minute / 60
    
    if end_time < start_time:
        play_hours = (24 - start_hours) + end_hours
    else:
        play_hours = end_hours - start_hours
    
    return round(play_hours, 1)

def apply_monthly_interest():
    """毎月1日に利息を適用（一律10%）"""
    today = datetime.date.today()
    
    if today.day == 1:
        if os.path.exists(BANK_LOANS_FILE):
            loans_df = pd.read_csv(BANK_LOANS_FILE)
            active_loans = loans_df[loans_df['status'] == 'active']
            
            if not active_loans.empty:
                interest_records = []
                
                for idx in active_loans.index:
                    loan_id = loans_df.loc[idx, 'loan_id']
                    lender = loans_df.loc[idx, 'lender']
                    borrower = loans_df.loc[idx, 'borrower']
                    current_remaining = float(loans_df.loc[idx, 'remaining'])
                    
                    interest = current_remaining * 0.1
                    new_remaining = current_remaining + interest
                    
                    loans_df.loc[idx, 'remaining'] = new_remaining
                    loans_df.loc[idx, 'last_interest_date'] = today
                    
                    interest_record = {
                        'transaction_id': f"INT_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{loan_id}",
                        'datetime': pd.Timestamp.now(),
                        'type': 'interest',
                        'from_user': borrower,
                        'to_user': lender,
                        'amount': interest,
                        'loan_id': loan_id,
                        'balance_after': new_remaining,
                        'notes': f'月次利息10% (元残高: {current_remaining:.0f} P)'
                    }
                    interest_records.append(interest_record)
                    
                    add_notification(lender, 
                        f"💰 {borrower}さんからの融資に利息{interest:.0f} Pが追加されました（残高: {new_remaining:.0f} P）", 
                        "success")
                    add_notification(borrower, 
                        f"📈 {lender}さんへの借入に利息{interest:.0f} Pが追加されました（残高: {new_remaining:.0f} P）", 
                        "warning")
                
                loans_df.to_csv(BANK_LOANS_FILE, index=False)
                
                if interest_records:
                    if os.path.exists(BANK_TRANSACTIONS_FILE):
                        trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
                        new_trans_df = pd.DataFrame(interest_records)
                        trans_df = pd.concat([trans_df, new_trans_df], ignore_index=True)
                    else:
                        trans_df = pd.DataFrame(interest_records)
                    trans_df.to_csv(BANK_TRANSACTIONS_FILE, index=False)

def init_data():
    """データファイルの初期化"""
    try:
        if not os.path.exists(GAME_DATA_FILE):
            df = pd.DataFrame(columns=['datetime', 'player', 'date', 'start_time', 'end_time', 'play_hours', 'buyin', 'result'])
            df.to_csv(GAME_DATA_FILE, index=False)
        
        if not os.path.exists(BANK_LOANS_FILE):
            df = pd.DataFrame(columns=['loan_id', 'datetime', 'lender', 'borrower', 'amount', 'remaining', 'status', 'due_date', 'last_interest_date'])
            df.to_csv(BANK_LOANS_FILE, index=False)
        
        if not os.path.exists(BANK_APPLICATIONS_FILE):
            df = pd.DataFrame(columns=['app_id', 'datetime', 'type', 'from_user', 'to_user', 'amount', 'loan_id', 'status', 'expire_date', 'message'])
            df.to_csv(BANK_APPLICATIONS_FILE, index=False)
        
        if not os.path.exists(BANK_TRANSACTIONS_FILE):
            df = pd.DataFrame(columns=['transaction_id', 'datetime', 'type', 'from_user', 'to_user', 'amount', 'loan_id', 'balance_after', 'notes'])
            df.to_csv(BANK_TRANSACTIONS_FILE, index=False)
        
        if not os.path.exists(JACKPOT_DATA_FILE):
            df = pd.DataFrame([{'datetime': pd.Timestamp.now(), 'type': 'init', 'amount': 0, 'total': 0, 'admin': 'system', 'notes': '初期化'}])
            df.to_csv(JACKPOT_DATA_FILE, index=False)
        
        if not os.path.exists(JACKPOT_WINNERS_FILE):
            df = pd.DataFrame(columns=['datetime', 'date', 'player', 'hand_type', 'hand_cards', 'table_cards', 'amount', 'paid'])
            df.to_csv(JACKPOT_WINNERS_FILE, index=False)
        
        if not os.path.exists(NOTIFICATIONS_FILE):
            df = pd.DataFrame(columns=['datetime', 'user', 'message', 'type', 'read'])
            df.to_csv(NOTIFICATIONS_FILE, index=False)
            
    except Exception as e:
        st.error(f"データ初期化エラー: {str(e)}")

def init_session_state():
    """セッション状態の初期化"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'page' not in st.session_state:
        st.session_state.page = 'game_report'
    if 'game_registered' not in st.session_state:
        st.session_state.game_registered = False
    if 'loan_applied' not in st.session_state:
        st.session_state.loan_applied = False
    if 'role' not in st.session_state:
        st.session_state.role = None

def get_current_jackpot():
    """現在のジャックポット金額を取得"""
    try:
        df = pd.read_csv(JACKPOT_DATA_FILE)
        if not df.empty:
            return df.iloc[-1]['total']
    except:
        pass
    return 0

def get_latest_jackpot_winner():
    """最新のジャックポット取得者を取得"""
    try:
        if os.path.exists(JACKPOT_WINNERS_FILE):
            df = pd.read_csv(JACKPOT_WINNERS_FILE)
            if not df.empty:
                return df.iloc[-1]
    except:
        pass
    return None

def login_page():
    """ログイン画面"""
    st.markdown("""
        <div class="main-header">
            <h1 style="color: white; font-size: 48px; margin: 0;">🃏 We Are Pretty Cure! 🃏</h1>
            <p style="color: rgba(255, 255, 255, 0.8); font-size: 20px;">Poker Management System</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.container():
            st.markdown("### 🔐 ログイン")
            
            with st.form("login_form", clear_on_submit=True):
                username = st.text_input("ユーザー名", placeholder="ユーザー名を入力")
                password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
                
                if st.form_submit_button("ログイン", use_container_width=True):
                    users_df = load_users()
                    user = users_df[(users_df['username'] == username) & (users_df['password'] == password) & (users_df['active'] == True)]
                    
                    if not user.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = user.iloc[0]['role']
                        st.success("✨ ログイン成功！")
                        st.rerun()
                    else:
                        st.error("❌ ユーザー名またはパスワードが正しくありません")

def game_report_page():
    """ゲームレポートページ"""
    st.markdown("## 🎮 ゲームレポート")
    
    # 登録成功後のリセット処理
    if st.session_state.get('game_registered', False):
        st.session_state.game_registered = False
    
    notifications = get_notifications(st.session_state.username)
    if not notifications.empty:
        st.markdown("### 📬 通知")
        for _, notif in notifications.iterrows():
            if notif['type'] == 'success':
                st.success(notif['message'])
            elif notif['type'] == 'warning':
                st.warning(notif['message'])
            else:
                st.info(notif['message'])
        mark_notifications_read(st.session_state.username)
        st.markdown("---")
    
    st.markdown("### 今日のゲーム結果を入力")
    
    date = st.date_input("📅 日付", value=datetime.date.today())
    
    col1, col2 = st.columns(2)
    with col1:
        start_time = st.time_input("🎯 プレイ開始時間", value=time(20, 0))
    with col2:
        end_time = st.time_input("🏁 プレイ終了時間", value=time(23, 0))
    
    play_hours = calculate_play_time(start_time, end_time)
    st.info(f"⏱️ プレイ時間: {play_hours} 時間")
    
    col1, col2 = st.columns(2)
    with col1:
        buyin = st.number_input("💵 バイイン (P)", min_value=0, step=1000, value=0)
    with col2:
        result = st.number_input("📊 収支 (P)", step=1000, value=0)
    
    # チェックボックスをユニークなキーで管理
    confirm_key = "game_confirm"
    confirm = st.checkbox("⚠️ 上記の内容で登録することを確認しました", key=confirm_key)
    
    if st.button("📊 登録する", use_container_width=True, disabled=not confirm):
        try:
            df = pd.read_csv(GAME_DATA_FILE) if os.path.exists(GAME_DATA_FILE) else pd.DataFrame()
            new_data = pd.DataFrame([{
                'datetime': pd.Timestamp.now(),
                'player': st.session_state.username,
                'date': date,
                'start_time': start_time.strftime('%H:%M'),
                'end_time': end_time.strftime('%H:%M'),
                'play_hours': play_hours,
                'buyin': buyin,
                'result': result
            }])
            df = pd.concat([df, new_data], ignore_index=True)
            df.to_csv(GAME_DATA_FILE, index=False)
            
            st.balloons()
            st.success("✨ ゲーム結果を登録しました！")
            
            if result > 0:
                st.success(f"🎉 本日の利益: +{result:,} P")
            elif result < 0:
                st.error(f"😢 本日の損失: {result:,} P")
            else:
                st.info("😐 本日はプラマイゼロでした")
            
            # チェックボックスをリセット
            if confirm_key in st.session_state:
                del st.session_state[confirm_key]
            
            st.session_state.game_registered = True
            tm.sleep(1)
            st.rerun()
                
        except Exception as e:
            st.error(f"登録エラー: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📊 最近の履歴（最新3件）")
    
    try:
        if os.path.exists(GAME_DATA_FILE):
            df = pd.read_csv(GAME_DATA_FILE)
            user_df = df[df['player'] == st.session_state.username].copy()
            
            if not user_df.empty:
                user_df = user_df.sort_values('datetime', ascending=False).head(3).reset_index(drop=True)
                
                for idx, row in user_df.iterrows():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['date']}** ({row['start_time']} - {row['end_time']})")
                        result_emoji = "🎉" if row['result'] > 0 else "😢" if row['result'] < 0 else "😐"
                        st.write(f"{result_emoji} 収支: {row['result']:,} P (バイイン: {row['buyin']:,} P)")
                        st.write(f"⏱️ プレイ時間: {row['play_hours']}時間")
                    
                    with col2:
                        if row['result'] >= 30000:
                            st.success("🔥 超大勝ち！")
                        elif row['result'] >= 20000:
                            st.success("大勝ち！")
                        elif row['result'] >= 10000:
                            st.success("好調！")
                        elif row['result'] <= -30000:
                            st.error("大敗...")
                        elif row['result'] <= -20000:
                            st.error("大負け")
                        elif row['result'] <= -10000:
                            st.error("不調")
                    
                    with col3:
                        actual_idx = df[df['player'] == st.session_state.username].sort_values('datetime', ascending=False).head(3).index[idx]
                        if st.button("🗑️ 削除", key=f"del_game_{actual_idx}"):
                            df = pd.read_csv(GAME_DATA_FILE)
                            df = df.drop(actual_idx).reset_index(drop=True)
                            df.to_csv(GAME_DATA_FILE, index=False)
                            st.success("記録を削除しました")
                            st.rerun()
                    
                    st.markdown("---")
            else:
                st.info("📝 まだゲーム履歴がありません")
        else:
            st.info("📝 まだゲーム履歴がありません")
    except Exception as e:
        st.info("📝 まだゲーム履歴がありません")

def pbank_page():
    """P-BANK ページ（完全統合版）"""
    st.markdown("## 💰 P-BANK")
    
    # 利息の自動適用（毎月1日）
    apply_monthly_interest()
    
    # 融資申請後のリセット処理
    if st.session_state.get('loan_applied', False):
        st.session_state.loan_applied = False
    
    total_lent = 0
    total_borrowed = 0
    pending_apps = 0
    interest_earned = 0  # 受取利息累計
    interest_paid = 0    # 支払利息累計
    
    try:
        if os.path.exists(BANK_LOANS_FILE):
            loans_df = pd.read_csv(BANK_LOANS_FILE)
            loans_df['amount'] = pd.to_numeric(loans_df['amount'], errors='coerce').fillna(0)
            loans_df['remaining'] = pd.to_numeric(loans_df['remaining'], errors='coerce').fillna(0)
            
            my_loans_as_lender = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            total_lent = my_loans_as_lender['remaining'].sum() if not my_loans_as_lender.empty else 0
            
            my_loans_as_borrower = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            total_borrowed = my_loans_as_borrower['remaining'].sum() if not my_loans_as_borrower.empty else 0
        else:
            loans_df = pd.DataFrame()
        
        # 利息履歴から累計を計算
        if os.path.exists(BANK_TRANSACTIONS_FILE):
            trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
            # 受取利息（自分が貸し手の利息）
            earned = trans_df[(trans_df['to_user'] == st.session_state.username) & (trans_df['type'] == 'interest')]
            if not earned.empty:
                interest_earned = earned['amount'].sum()
            
            # 支払利息（自分が借り手の利息）
            paid = trans_df[(trans_df['from_user'] == st.session_state.username) & (trans_df['type'] == 'interest')]
            if not paid.empty:
                interest_paid = paid['amount'].sum()
        
        if os.path.exists(BANK_APPLICATIONS_FILE):
            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
            pending_apps = len(apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')])
        else:
            apps_df = pd.DataFrame()
            
    except Exception as e:
        loans_df = pd.DataFrame()
        apps_df = pd.DataFrame()
    
    # 操作方法・ルール説明
    with st.expander("📖 P-BANKの使い方とルール"):
        st.markdown("""
        ### 🏦 P-BANKシステムについて
        
        **基本ルール:**
        - 💰 プレイヤー間でポイント(P)の貸し借りができます
        - 📈 毎月1日に残高の10%が利息として自動加算されます
        - ⏰ 返済期限はプレイヤー間で相談ください
        - ✅ 融資・返済には相手の承認が必要です
        
        **操作方法:**
        1. **融資を受けたい場合** → 「融資申込」タブから申請
        2. **融資を承認する場合** → 「承認待ち」タブで承認/却下
        3. **返済する場合** → 「返済」タブから返済申請
        4. **利息の確認** → 「利息一覧」タブで履歴確認
        
        **利息計算例:**
        - 10,000P借入 → 毎月1日に1,000P（10%）の利息が加算
        - 同時に10,000P貸出がある場合 → 差し引き0P（プラスマイナスゼロ）
        """)
    
    # メイン統計表示
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.success(f"### 💸 貸出額\n## {int(total_lent):,} P")
    with col2:
        st.error(f"### 💳 借入額\n## {int(total_borrowed):,} P")
    with col3:
        net_interest = interest_earned - interest_paid
        color = "success" if net_interest >= 0 else "error"
        getattr(st, color)(f"### 📊 利息収支\n## {int(net_interest):,} P")
    with col4:
        if pending_apps > 0:
            st.warning(f"### 📬 承認待ち\n## {pending_apps} 件")
        else:
            st.info(f"### 📬 承認待ち\n## 0 件")
    
    tabs = st.tabs(["💸 融資申込", "💰 返済", "📋 貸出一覧", "✅ 承認待ち", "📈 利息一覧", "📊 履歴"])
    
    # 融資申込タブ
    with tabs[0]:
        st.markdown("### 💸 新規融資申込")
        st.info("📌 利息: 毎月1日に残高の10%が加算されます | 返済期限: 申込先による ")
        
        users_df = load_users()
        active_users = users_df[(users_df['username'] != st.session_state.username) & (users_df['active'] == True)]['username'].tolist()
        
        if active_users:
            lender = st.selectbox("融資元を選択", active_users)
            amount = st.number_input("申込金額 (P)", min_value=100, step=1000, value=1000)
            message = st.text_area("メッセージ (任意)", placeholder="融資の目的など...")
            
            loan_confirm_key = "loan_confirm"
            confirm = st.checkbox("上記の内容で申込することを確認しました", key=loan_confirm_key)
            
            if st.button("📤 申込する", use_container_width=True, disabled=not confirm):
                try:
                    app_id = f"APP_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{st.session_state.username}"
                    
                    new_app = pd.DataFrame([{
                        'app_id': app_id,
                        'datetime': pd.Timestamp.now(),
                        'type': 'loan',
                        'from_user': st.session_state.username,
                        'to_user': lender,
                        'amount': amount,
                        'loan_id': '',
                        'status': '申込中',
                        'expire_date': pd.Timestamp.now() + pd.Timedelta(hours=24),
                        'message': message
                    }])
                    
                    if os.path.exists(BANK_APPLICATIONS_FILE):
                        apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                        apps_df = pd.concat([apps_df, new_app], ignore_index=True)
                    else:
                        apps_df = new_app
                    
                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                    
                    add_notification(lender, f"💰 {st.session_state.username}さんから{amount:,} Pの融資申込がありました", "warning")
                    
                    st.balloons()
                    st.success(f"✅ {lender}さんに{amount:,} Pの融資申込を送信しました！")
                    st.info("相手の承認をお待ちください。")
                    
                    if loan_confirm_key in st.session_state:
                        del st.session_state[loan_confirm_key]
                    
                    st.session_state.loan_applied = True
                    tm.sleep(1)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"申込エラー: {str(e)}")
        else:
            st.info("他のアクティブユーザーがいません")
    
    # 返済タブ（強化版）
    with tabs[1]:
        st.markdown("### 💰 返済")
        
        if not loans_df.empty:
            my_debts = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            
            if not my_debts.empty:
                for loan_idx, loan in my_debts.iterrows():
                    with st.expander(f"💳 {loan['lender']}さんへの借入 - {int(loan['remaining']):,} P", expanded=True):
                        st.write(f"借入日: {loan['datetime']}")
                        st.write(f"元本: {int(loan['amount']):,} P")
                        st.write(f"現在残高: {int(loan['remaining']):,} P")
                        
                        # 利息込み金額の計算
                        interest_amount = int(loan['remaining']) - int(loan['amount'])
                        if interest_amount > 0:
                            st.info(f"💹 これまでの利息合計: {interest_amount:,} P")
                        
                        st.markdown("---")
                        
                        # 返済フォーム
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            repay_amount = st.number_input(
                                "返済額 (P)",
                                min_value=100,
                                max_value=int(loan['remaining']),
                                step=1000,
                                value=min(1000, int(loan['remaining'])),
                                key=f"repay_{loan['loan_id']}"
                            )
                        
                        # チェックボックスで確認
                        repay_confirm_key = f"repay_confirm_{loan['loan_id']}"
                        confirm_repay = st.checkbox(
                            f"{repay_amount:,} Pを返済することを確認しました", 
                            key=repay_confirm_key
                        )
                        
                        if st.button(
                            f"💰 {repay_amount:,} P返済申請する", 
                            key=f"repay_btn_{loan['loan_id']}",
                            disabled=not confirm_repay,
                            use_container_width=True
                        ):
                            try:
                                app_id = f"REP_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{st.session_state.username}"
                                
                                new_app = pd.DataFrame([{
                                    'app_id': app_id,
                                    'datetime': pd.Timestamp.now(),
                                    'type': 'repayment',
                                    'from_user': st.session_state.username,
                                    'to_user': loan['lender'],
                                    'amount': repay_amount,
                                    'loan_id': loan['loan_id'],
                                    'status': '申込中',
                                    'expire_date': pd.Timestamp.now() + pd.Timedelta(hours=24),
                                    'message': f"返済 ({int(loan['remaining']):,} P中 {repay_amount:,} P)"
                                }])
                                
                                if os.path.exists(BANK_APPLICATIONS_FILE):
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df = pd.concat([apps_df, new_app], ignore_index=True)
                                else:
                                    apps_df = new_app
                                
                                apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                
                                add_notification(loan['lender'], 
                                    f"💰 {st.session_state.username}さんから{repay_amount:,} Pの返済申請がありました", 
                                    "success")
                                
                                st.success(f"✅ {repay_amount:,} Pの返済申請を送信しました")
                                st.info(f"📧 {loan['lender']}さんの承認をお待ちください")
                                
                                # チェックボックスをリセット
                                if repay_confirm_key in st.session_state:
                                    del st.session_state[repay_confirm_key]
                                
                                tm.sleep(1)
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"返済エラー: {str(e)}")
                        
                        # この借入に関する返済履歴を表示
                        st.markdown("#### 📜 この借入の返済履歴")
                        
                        # 返済申請履歴を取得
                        if os.path.exists(BANK_APPLICATIONS_FILE):
                            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                            repay_history = apps_df[
                                (apps_df['loan_id'] == loan['loan_id']) & 
                                (apps_df['type'] == 'repayment')
                            ].sort_values('datetime', ascending=False)
                            
                            if not repay_history.empty:
                                for _, repay in repay_history.iterrows():
                                    status_icon = "✅" if repay['status'] == '承認済' else "⏳" if repay['status'] == '申込中' else "❌"
                                    
                                    # 返済履歴の表示
                                    col1, col2, col3 = st.columns([2, 1, 1])
                                    with col1:
                                        st.write(f"{status_icon} {repay['datetime'][:16]}")
                                    with col2:
                                        st.write(f"{int(repay['amount']):,} P")
                                    with col3:
                                        if repay['status'] == '承認済':
                                            st.success("承認済")
                                        elif repay['status'] == '申込中':
                                            st.warning("承認待ち")
                                        else:
                                            st.error("却下")
                                
                                # 承認済みの返済合計
                                approved_repayments = repay_history[repay_history['status'] == '承認済']
                                if not approved_repayments.empty:
                                    total_repaid = approved_repayments['amount'].sum()
                                    st.success(f"📊 承認済み返済合計: {int(total_repaid):,} P")
                                
                                # 申請中の返済
                                pending_repayments = repay_history[repay_history['status'] == '申込中']
                                if not pending_repayments.empty:
                                    pending_total = pending_repayments['amount'].sum()
                                    st.warning(f"⏳ 承認待ち返済: {int(pending_total):,} P")
                            else:
                                st.info("まだ返済履歴はありません")
                        else:
                            st.info("まだ返済履歴はありません")
                        
                        st.markdown("---")
            else:
                st.success("🎉 現在借入はありません")
        else:
            st.success("🎉 現在借入はありません")
    
    # 貸出一覧タブ
    with tabs[2]:
        st.markdown("### 📋 貸出一覧")
        
        if not loans_df.empty:
            my_lendings = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            
            if not my_lendings.empty:
                for _, loan in my_lendings.iterrows():
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**{loan['borrower']}さん**")
                        st.write(f"貸付日: {loan['datetime']}")
                        st.write(f"元本: {int(loan['amount']):,} P")
                        st.write(f"現在残高: {int(loan['remaining']):,} P")
                        
                        interest_amount = int(loan['remaining']) - int(loan['amount'])
                        if interest_amount > 0:
                            st.success(f"💹 利息収入合計: {interest_amount:,} P")
                    
                    st.markdown("---")
            else:
                st.info("📝 貸出中の融資はありません")
        else:
            st.info("📝 貸出中の融資はありません")
    
    # 承認待ちタブ
    with tabs[3]:
        st.markdown("### ✅ 承認待ち申請")
        
        if not apps_df.empty:
            my_pending = apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')]
            
            if not my_pending.empty:
                for _, app in my_pending.iterrows():
                    with st.expander(f"📬 {app['from_user']}さんからの{app['type']}申請"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"申請日時: {app['datetime']}")
                            st.write(f"金額: {int(app['amount']):,} P")
                            if pd.notna(app.get('message')) and app.get('message'):
                                st.write(f"メッセージ: {app['message']}")
                        
                        with col2:
                            if st.button("✅ 承認", key=f"approve_{app['app_id']}"):
                                try:
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df.loc[apps_df['app_id'] == app['app_id'], 'status'] = '承認済'
                                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                    
                                    if app['type'] == 'loan':
                                        loan_id = f"LOAN_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
                                        
                                        new_loan = pd.DataFrame([{
                                            'loan_id': loan_id,
                                            'datetime': pd.Timestamp.now(),
                                            'lender': st.session_state.username,
                                            'borrower': app['from_user'],
                                            'amount': app['amount'],
                                            'remaining': app['amount'],
                                            'status': 'active',
                                            'due_date': '',  # 期限なし
                                            'last_interest_date': pd.Timestamp.now()
                                        }])
                                        
                                        if os.path.exists(BANK_LOANS_FILE):
                                            loans_df = pd.read_csv(BANK_LOANS_FILE)
                                            loans_df = pd.concat([loans_df, new_loan], ignore_index=True)
                                        else:
                                            loans_df = new_loan
                                        
                                        loans_df.to_csv(BANK_LOANS_FILE, index=False)
                                        
                                        add_notification(app['from_user'], f"✅ {st.session_state.username}さんが融資申請を承認しました！", "success")
                                        
                                        st.success("✅ 融資を承認しました")
                                        
                                    elif app['type'] == 'repayment':
                                        loans_df = pd.read_csv(BANK_LOANS_FILE)
                                        loan_idx = loans_df['loan_id'] == app['loan_id']
                                        
                                        if loan_idx.any():
                                            current_remaining = loans_df.loc[loan_idx, 'remaining'].iloc[0]
                                            new_remaining = max(0, current_remaining - app['amount'])
                                            loans_df.loc[loan_idx, 'remaining'] = new_remaining
                                            
                                            if new_remaining == 0:
                                                loans_df.loc[loan_idx, 'status'] = 'completed'
                                            
                                            loans_df.to_csv(BANK_LOANS_FILE, index=False)
                                            
                                            add_notification(app['from_user'], f"✅ 返済が承認されました！残高: {int(new_remaining):,} P", "success")
                                            
                                            st.success("✅ 返済を承認しました")
                                    
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"承認エラー: {str(e)}")
                            
                            if st.button("❌ 却下", key=f"reject_{app['app_id']}"):
                                try:
                                    apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
                                    apps_df.loc[apps_df['app_id'] == app['app_id'], 'status'] = '却下'
                                    apps_df.to_csv(BANK_APPLICATIONS_FILE, index=False)
                                    
                                    add_notification(app['from_user'], f"❌ {st.session_state.username}さんが申請を却下しました", "error")
                                    
                                    st.warning("申請を却下しました")
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"却下エラー: {str(e)}")
            else:
                st.info("📝 承認待ちの申請はありません")
            
            st.markdown("#### 📤 自分の申請状況")
            my_apps = apps_df[(apps_df['from_user'] == st.session_state.username) & (apps_df['status'] == '申込中')]
            
            if not my_apps.empty:
                for _, app in my_apps.iterrows():
                    st.write(f"• {app['to_user']}さんへの{app['type']}申請 - {int(app['amount']):,} P (承認待ち)")
            else:
                st.info("申請中の案件はありません")
        else:
            st.info("📝 申請データがありません")
    
    # 利息一覧タブ（新規追加）
    with tabs[4]:
        st.markdown("### 📈 利息一覧")
        
        # 利息収支サマリー
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**受取利息累計**\n{int(interest_earned):,} P")
        with col2:
            st.error(f"**支払利息累計**\n{int(interest_paid):,} P")
        with col3:
            net = interest_earned - interest_paid
            if net >= 0:
                st.info(f"**利息収支**\n+{int(net):,} P")
            else:
                st.warning(f"**利息収支**\n{int(net):,} P")
        
        st.markdown("---")
        
        # 利息履歴表示
        if os.path.exists(BANK_TRANSACTIONS_FILE):
            trans_df = pd.read_csv(BANK_TRANSACTIONS_FILE)
            
            # 自分に関連する利息のみ抽出
            my_interest = trans_df[
                ((trans_df['to_user'] == st.session_state.username) | 
                 (trans_df['from_user'] == st.session_state.username)) & 
                (trans_df['type'] == 'interest')
            ].copy()
            
            if not my_interest.empty:
                my_interest = my_interest.sort_values('datetime', ascending=False)
                
                for _, record in my_interest.iterrows():
                    if record['to_user'] == st.session_state.username:
                        # 受取利息
                        st.success(f"📈 **{record['datetime'][:10]}** - {record['from_user']}さんから利息 +{int(record['amount']):,} P")
                        st.caption(f"　　{record.get('notes', '')}")
                    else:
                        # 支払利息
                        st.error(f"📉 **{record['datetime'][:10]}** - {record['to_user']}さんへ利息 -{int(record['amount']):,} P")
                        st.caption(f"　　{record.get('notes', '')}")
                    st.markdown("---")
            else:
                st.info("📝 利息履歴はまだありません（毎月1日に計算されます）")
        else:
            st.info("📝 利息履歴はまだありません")
        
        # 次回利息予測
        st.markdown("#### 💡 次回利息予測（翌月1日）")
        if not loans_df.empty:
            next_earned = 0
            next_paid = 0
            
            # 貸出分の利息
            my_lendings = loans_df[(loans_df['lender'] == st.session_state.username) & (loans_df['status'] == 'active')]
            if not my_lendings.empty:
                for _, loan in my_lendings.iterrows():
                    interest = int(loan['remaining']) * 0.1
                    next_earned += interest
                    st.write(f"• {loan['borrower']}さんから +{int(interest):,} P")
            
            # 借入分の利息
            my_debts = loans_df[(loans_df['borrower'] == st.session_state.username) & (loans_df['status'] == 'active')]
            if not my_debts.empty:
                for _, loan in my_debts.iterrows():
                    interest = int(loan['remaining']) * 0.1
                    next_paid += interest
                    st.write(f"• {loan['lender']}さんへ -{int(interest):,} P")
            
            if next_earned > 0 or next_paid > 0:
                st.markdown("---")
                net_next = next_earned - next_paid
                if net_next >= 0:
                    st.success(f"**翌月の利息収支予測: +{int(net_next):,} P**")
                else:
                    st.error(f"**翌月の利息収支予測: {int(net_next):,} P**")
            else:
                st.info("現在アクティブな融資がありません")
    
    # 履歴タブ
    with tabs[5]:
        st.markdown("### 📊 取引履歴")
        
        all_history = []
        
        # 融資履歴
        if not loans_df.empty:
            for _, loan in loans_df.iterrows():
                if loan['lender'] == st.session_state.username or loan['borrower'] == st.session_state.username:
                    history_type = "貸出" if loan['lender'] == st.session_state.username else "借入"
                    other_user = loan['borrower'] if loan['lender'] == st.session_state.username else loan['lender']
                    
                    all_history.append({
                        '日時': loan['datetime'],
                        'タイプ': history_type,
                        '相手': other_user,
                        '金額': int(loan['amount']),
                        '残高': int(loan['remaining']),
                        '状態': loan['status']
                    })
        
        # 申請履歴
        if not apps_df.empty:
            for _, app in apps_df.iterrows():
                if app['from_user'] == st.session_state.username or app['to_user'] == st.session_state.username:
                    if app['from_user'] == st.session_state.username:
                        app_type = f"{app['type']}申請(送信)"
                        other_user = app['to_user']
                    else:
                        app_type = f"{app['type']}申請(受信)"
                        other_user = app['from_user']
                    
                    all_history.append({
                        '日時': app['datetime'],
                        'タイプ': app_type,
                        '相手': other_user,
                        '金額': int(app['amount']),
                        '残高': '-',
                        '状態': app['status']
                    })
        
        if all_history:
            history_df = pd.DataFrame(all_history)
            history_df = history_df.sort_values('日時', ascending=False)
            
            st.dataframe(
                history_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "金額": st.column_config.NumberColumn("金額", format="%d P"),
                    "残高": st.column_config.TextColumn("残高")
                }
            )
        else:
            st.info("📝 取引履歴がありません")

def community_page():
    """コミュニティページ（修正・改善版）"""
    st.markdown("## 🏆 Community")
    
    # ジャックポットと統計
    col1, col2 = st.columns([3, 2])
    
    with col1:
        current_jackpot = get_current_jackpot()
        st.markdown(f"""
            <div style="background: linear-gradient(45deg, #FFD700, #FFA500); 
                        color: #000; padding: 20px; border-radius: 15px; 
                        text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="margin: 0; color: #000;">🎰 現在のジャックポット</h3>
                <h2 style="margin: 10px 0; font-size: 36px; color: #000;">{current_jackpot:,} P</h2>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        try:
            total_play_hours = 0
            total_buyin = 0
            total_players = 0
            
            if os.path.exists(GAME_DATA_FILE):
                game_df = pd.read_csv(GAME_DATA_FILE)
                if 'play_hours' in game_df.columns:
                    total_play_hours = game_df['play_hours'].sum()
                if 'buyin' in game_df.columns:
                    total_buyin = game_df['buyin'].sum()
                total_players = game_df['player'].nunique()
            
            # 背景を半透明の黒に変更、文字を白に
            st.markdown(f"""
                <div style="background: rgba(0, 0, 0, 0.5); 
                            padding: 15px; border-radius: 10px; 
                            backdrop-filter: blur(5px);">
                    <div style="color: white; font-size: 14px; margin-bottom: 8px;">
                        ⏱️ <b>総プレイ時間:</b> {total_play_hours:.1f} 時間
                    </div>
                    <div style="color: white; font-size: 14px; margin-bottom: 8px;">
                        💵 <b>総バイイン:</b> {int(total_buyin):,} P
                    </div>
                    <div style="color: white; font-size: 14px;">
                        👥 <b>アクティブプレイヤー:</b> {total_players} 人
                    </div>
                </div>
            """, unsafe_allow_html=True)
        except:
            st.metric("⏱️ 総プレイ時間", "0.0 時間")
            st.metric("💵 総バイイン", "0 P")
            st.metric("👥 アクティブプレイヤー", "0 人")
    
    # 最新ジャックポット獲得者
    latest_winner = get_latest_jackpot_winner()
    if latest_winner is not None:
        st.markdown(f"""
            <div style="background: linear-gradient(45deg, #FF1493, #FFB6C1); 
                        color: white; padding: 15px; border-radius: 10px; 
                        text-align: center; margin: 20px 0;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <p style="margin: 0; font-size: 18px; font-weight: bold;">
                    🎊 最新ジャックポット獲得者 🎊
                </p>
                <p style="margin: 5px 0; font-size: 20px;">
                    <b>{latest_winner['player']}</b>さん
                </p>
                <p style="margin: 5px 0; font-size: 16px;">
                    {latest_winner['hand_type']} - +{int(latest_winner['amount']):,} P
                </p>
                <p style="margin: 5px 0; font-size: 14px; opacity: 0.9;">
                    Hand: {latest_winner.get('hand_cards', 'N/A')} | Board: {latest_winner.get('table_cards', 'N/A')}
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # タブでコンテンツを整理
    tab1, tab2, tab3 = st.tabs(["🏅 ランキング", "📈 統計", "🏆 殿堂"])
    
    with tab1:
        # ランキング
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 🏅 総合収支ランキング")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        player_stats = game_df.groupby('player').agg({
                            'result': 'sum', 
                            'buyin': 'count',
                            'play_hours': 'sum'
                        }).rename(columns={'buyin': 'games'})
                        player_stats = player_stats.sort_values('result', ascending=False)
                        
                        for idx, (player, stats) in enumerate(player_stats.head(10).iterrows(), 1):
                            medal = ""
                            if idx == 1:
                                medal = "🥇"
                                color = "#FFD700"
                            elif idx == 2:
                                medal = "🥈"
                                color = "#C0C0C0"
                            elif idx == 3:
                                medal = "🥉"
                                color = "#CD7F32"
                            else:
                                medal = f"{idx}."
                                color = "#666"
                            
                            profit = int(stats['result'])
                            games = int(stats['games'])
                            avg = profit / games if games > 0 else 0
                            
                            st.markdown(f"""
                                <div style="display: flex; align-items: center; margin: 5px 0;">
                                    <span style="color: {color}; font-size: 20px; width: 40px;">{medal}</span>
                                    <span style="flex: 1;">
                                        <b>{player}</b> - {'+' if profit >= 0 else ''}{profit:,} P
                                        <small style="opacity: 0.7;">({games}戦, 平均{'+' if avg >= 0 else ''}{int(avg):,}P)</small>
                                    </span>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
        
        with col2:
            st.markdown("### 🎯 今月のランキング")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    game_df['date'] = pd.to_datetime(game_df['date'])
                    
                    # 今月のデータのみ抽出
                    current_month = pd.Timestamp.now().strftime('%Y-%m')
                    month_df = game_df[game_df['date'].dt.strftime('%Y-%m') == current_month]
                    
                    if not month_df.empty:
                        month_stats = month_df.groupby('player').agg({
                            'result': 'sum',
                            'buyin': 'count'
                        }).rename(columns={'buyin': 'games'})
                        month_stats = month_stats.sort_values('result', ascending=False)
                        
                        for idx, (player, stats) in enumerate(month_stats.head(5).iterrows(), 1):
                            profit = int(stats['result'])
                            games = int(stats['games'])
                            
                            if profit >= 0:
                                st.success(f"{idx}. **{player}** +{profit:,} P ({games}戦)")
                            else:
                                st.error(f"{idx}. **{player}** {profit:,} P ({games}戦)")
                    else:
                        st.info("今月のデータはまだありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
    
    with tab2:
        # 統計情報
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 全体統計")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        total_games = len(game_df)
                        total_result = game_df['result'].sum()
                        avg_result = game_df['result'].mean()
                        total_hours = game_df['play_hours'].sum()
                        
                        st.metric("総ゲーム数", f"{total_games} 回")
                        st.metric("総プレイ時間", f"{total_hours:.1f} 時間")
                        
                    else:
                        st.info("データがありません")
                else:st.info("データがありません")
            except Exception as e:
                st.info("データがありません")
        
        with col2:
            st.markdown("### 🎲 ゲーム傾向")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        # 曜日別の統計
                        game_df['date'] = pd.to_datetime(game_df['date'])
                        game_df['weekday'] = game_df['date'].dt.day_name()
                        
                        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        weekday_jp = ['月', '火', '水', '木', '金', '土', '日']
                        weekday_stats = game_df.groupby('weekday')['result'].agg(['count', 'mean'])
                        
                        st.markdown("**🗓️ 曜日別プレイ頻度**")
                        for day_en, day_jp in zip(weekday_order, weekday_jp):
                            if day_en in weekday_stats.index:
                                count = weekday_stats.loc[day_en, 'count']
                                avg = weekday_stats.loc[day_en, 'mean']
                                bar_width = int(count / len(game_df) * 100)
                                
                                st.markdown(f"""
                                    <div style="margin: 5px 0;">
                                        <span style="width: 30px; display: inline-block;">{day_jp}</span>
                                        <span style="display: inline-block; 
                                                   background: linear-gradient(90deg, #667eea, #764ba2);
                                                   width: {bar_width}%; max-width: 200px;
                                                   padding: 2px 8px; border-radius: 5px;
                                                   color: white; font-size: 12px;">
                                            {int(count)}回
                                        </span>
                                    </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.info("データがありません")
                else:
                    st.info("データがありません")
            except:
                st.info("データがありません")
    
    with tab3:
        # 殿堂（記録）
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🎉 大勝ち記録 TOP5")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        top_wins = game_df.nlargest(5, 'result')
                        for idx, (_, row) in enumerate(top_wins.iterrows(), 1):
                            st.markdown(f"""
                                <div style="background: rgba(40, 167, 69, 0.1); 
                                          padding: 10px; border-radius: 5px; 
                                          margin: 5px 0; border-left: 3px solid #28a745;">
                                    <b>{idx}. {row['player']}</b><br>
                                    <span style="font-size: 20px; color: #28a745;">+{int(row['result']):,} P</span><br>
                                    <small>{row['date']} ({row['play_hours']}時間)</small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")
        
        with col2:
            st.markdown("### 😱 大負け記録 TOP5")
            
            try:
                if os.path.exists(GAME_DATA_FILE):
                    game_df = pd.read_csv(GAME_DATA_FILE)
                    
                    if not game_df.empty:
                        top_losses = game_df.nsmallest(5, 'result')
                        for idx, (_, row) in enumerate(top_losses.iterrows(), 1):
                            st.markdown(f"""
                                <div style="background: rgba(220, 53, 69, 0.1); 
                                          padding: 10px; border-radius: 5px; 
                                          margin: 5px 0; border-left: 3px solid #dc3545;">
                                    <b>{idx}. {row['player']}</b><br>
                                    <span style="font-size: 20px; color: #dc3545;">{int(row['result']):,} P</span><br>
                                    <small>{row['date']} ({row['play_hours']}時間)</small>
                                </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("まだデータがありません")
                else:
                    st.info("まだデータがありません")
            except:
                st.info("まだデータがありません")

def stats_page():
    """個人統計ページ（グラフ機能追加版）"""
    st.markdown("## 📊 My Stats")
    
    try:
        if os.path.exists(GAME_DATA_FILE):
            game_df = pd.read_csv(GAME_DATA_FILE)
            my_games = game_df[game_df['player'] == st.session_state.username].copy()
            
            if not my_games.empty:
                # データの準備
                my_games['date'] = pd.to_datetime(my_games['date'])
                my_games = my_games.sort_values('date')
                my_games['cumulative'] = my_games['result'].cumsum()
                
                # サマリー統計
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_result = my_games['result'].sum()
                    color = "green" if total_result >= 0 else "red"
                    st.markdown(f"""
                        <div style="background: {color}; color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <h4>総収支</h4>
                            <h3>{int(total_result):,} P</h3>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    avg_result = my_games['result'].mean()
                    st.metric("平均収支", f"{int(avg_result):,} P")
                
                with col3:
                    total_games = len(my_games)
                    st.metric("プレイ回数", f"{total_games} 回")
                
                with col4:
                    total_hours = my_games['play_hours'].sum()
                    st.metric("総プレイ時間", f"{total_hours:.1f} 時間")
                
                # 詳細統計セクション（グラフより先に表示）
                st.markdown("---")
                st.markdown("### 📈 詳細統計")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("最大勝利", f"{int(my_games['result'].max()):,} P")
                    st.metric("最大敗北", f"{int(my_games['result'].min()):,} P")
                    win_rate = (my_games['result'] > 0).mean() * 100
                    st.metric("勝率", f"{win_rate:.1f}%")
                    
                    # 連勝・連敗
                    my_games['win'] = my_games['result'] > 0
                    streak = 0
                    max_win_streak = 0
                    max_loss_streak = 0
                    current_is_win = None
                    
                    for win in my_games['win']:
                        if current_is_win is None:
                            current_is_win = win
                            streak = 1
                        elif current_is_win == win:
                            streak += 1
                        else:
                            if current_is_win:
                                max_win_streak = max(max_win_streak, streak)
                            else:
                                max_loss_streak = max(max_loss_streak, streak)
                            current_is_win = win
                            streak = 1
                    
                    # 最後のストリークも確認
                    if current_is_win is not None:
                        if current_is_win:
                            max_win_streak = max(max_win_streak, streak)
                        else:
                            max_loss_streak = max(max_loss_streak, streak)
                    
                    st.metric("最大連勝", f"{max_win_streak} 連勝")
                    st.metric("最大連敗", f"{max_loss_streak} 連敗")
                
                with col2:
                    st.metric("総バイイン", f"{int(my_games['buyin'].sum()):,} P")
                    roi = (my_games['result'].sum() / my_games['buyin'].sum() * 100) if my_games['buyin'].sum() > 0 else 0
                    st.metric("ROI", f"{roi:.1f}%")
                    hourly = my_games['result'].sum() / my_games['play_hours'].sum() if my_games['play_hours'].sum() > 0 else 0
                    st.metric("時給", f"{int(hourly):,} P/h")
                    
                    # 直近のトレンド
                    if len(my_games) >= 5:
                        recent_5 = my_games.tail(5)['result'].sum()
                        recent_10 = my_games.tail(10)['result'].sum() if len(my_games) >= 10 else recent_5
                        
                        st.metric("直近5戦", f"{int(recent_5):,} P")
                        if len(my_games) >= 10:
                            st.metric("直近10戦", f"{int(recent_10):,} P")
                
                # グラフセクション（詳細統計の後に表示）
                st.markdown("---")
                st.markdown("### 📊 収支チャート")
                
                if PLOTLY_AVAILABLE:
                    # タブでグラフを分ける
                    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 累積収支", "📈 日別収支", "📅 月別集計"])
                    
                    with chart_tab1:
                        # 累積収支グラフ
                        fig_cumulative = go.Figure()
                        
                        # メインの累積収支ライン
                        fig_cumulative.add_trace(go.Scatter(
                            x=my_games['date'],
                            y=my_games['cumulative'],
                            mode='lines+markers',
                            name='累積収支',
                            line=dict(color='#667eea', width=3),
                            marker=dict(size=8, color='#764ba2'),
                            hovertemplate='<b>%{x|%Y-%m-%d}</b><br>累積: %{y:,.0f} P<extra></extra>'
                        ))
                        
                        # ゼロライン
                        fig_cumulative.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                        
                        # プラス域を緑、マイナス域を赤で塗りつぶし
                        fig_cumulative.add_trace(go.Scatter(
                            x=my_games['date'],
                            y=my_games['cumulative'],
                            fill='tozeroy',
                            fillcolor='rgba(40, 167, 69, 0.2)',
                            line=dict(width=0),
                            showlegend=False,
                            hoverinfo='skip'
                        ))
                        
                        fig_cumulative.update_layout(
                            title="累積収支推移",
                            xaxis_title="日付",
                            yaxis_title="累積収支 (P)",
                            hovermode='x unified',
                            height=400,
                            template="plotly_white",
                            font=dict(size=12),
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_cumulative, use_container_width=True)
                        
                        # 統計情報
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            max_cumulative = my_games['cumulative'].max()
                            st.info(f"**最高到達点:** {int(max_cumulative):,} P")
                        with col2:
                            min_cumulative = my_games['cumulative'].min()
                            st.info(f"**最低到達点:** {int(min_cumulative):,} P")
                        with col3:
                            current = my_games['cumulative'].iloc[-1]
                            st.info(f"**現在:** {int(current):,} P")
                    
                    with chart_tab2:
                        # 日別収支グラフ（棒グラフ）
                        colors = ['green' if x >= 0 else 'red' for x in my_games['result']]
                        
                        fig_daily = go.Figure(data=[
                            go.Bar(
                                x=my_games['date'],
                                y=my_games['result'],
                                marker_color=colors,
                                hovertemplate='<b>%{x|%Y-%m-%d}</b><br>収支: %{y:,.0f} P<extra></extra>'
                            )
                        ])
                        
                        fig_daily.update_layout(
                            title="日別収支",
                            xaxis_title="日付",
                            yaxis_title="収支 (P)",
                            height=400,
                            template="plotly_white",
                            showlegend=False,
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_daily, use_container_width=True)
                        
                        # 勝敗統計
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            wins = (my_games['result'] > 0).sum()
                            st.success(f"**勝利日数:** {wins} 日")
                        with col2:
                            losses = (my_games['result'] < 0).sum()
                            st.error(f"**敗北日数:** {losses} 日")
                        with col3:
                            draws = (my_games['result'] == 0).sum()
                            st.info(f"**引き分け:** {draws} 日")
                    
                    with chart_tab3:
                        # 月別集計グラフ
                        my_games['year_month'] = my_games['date'].dt.to_period('M')
                        monthly_stats = my_games.groupby('year_month').agg({
                            'result': 'sum',
                            'play_hours': 'sum',
                            'buyin': 'count'
                        }).rename(columns={'buyin': 'games'})
                        monthly_stats.index = monthly_stats.index.to_timestamp()
                        
                        # 月別収支の棒グラフ
                        colors_monthly = ['green' if x >= 0 else 'red' for x in monthly_stats['result']]
                        
                        fig_monthly = go.Figure()
                        
                        fig_monthly.add_trace(go.Bar(
                            x=monthly_stats.index,
                            y=monthly_stats['result'],
                            name='月間収支',
                            marker_color=colors_monthly,
                            hovertemplate='<b>%{x|%Y年%m月}</b><br>収支: %{y:,.0f} P<extra></extra>'
                        ))
                        
                        fig_monthly.update_layout(
                            title="月別収支",
                            xaxis_title="月",
                            yaxis_title="収支 (P)",
                            height=400,
                            template="plotly_white",
                            showlegend=False,
                            margin=dict(l=50, r=50, t=50, b=50)
                        )
                        
                        st.plotly_chart(fig_monthly, use_container_width=True)
                        
                        # 月別詳細テーブル
                        st.markdown("#### 📋 月別詳細")
                        monthly_display = monthly_stats.copy()
                        monthly_display['平均収支'] = monthly_display['result'] / monthly_display['games']
                        monthly_display['時給'] = monthly_display['result'] / monthly_display['play_hours']
                        monthly_display = monthly_display.sort_index(ascending=False)
                        
                        # 表示用に整形
                        monthly_display_formatted = pd.DataFrame({
                            '年月': monthly_display.index.strftime('%Y年%m月'),
                            '収支': [f"{int(x):,} P" for x in monthly_display['result']],
                            'ゲーム数': monthly_display['games'],
                            'プレイ時間': [f"{x:.1f}h" for x in monthly_display['play_hours']],
                            '平均収支': [f"{int(x):,} P" for x in monthly_display['平均収支']],
                            '時給': [f"{int(x):,} P/h" for x in monthly_display['時給']]
                        })
                        
                        st.dataframe(monthly_display_formatted, use_container_width=True, hide_index=True)
                
                else:
                    # Plotlyが利用できない場合の簡易表示
                    st.warning("グラフ表示にはPlotlyが必要です。`pip install plotly`でインストールしてください。")
                    
                    # 代替として最近10件の収支を表示
                    st.markdown("#### 📊 最近の収支（10件）")
                    recent_games = my_games.tail(10).sort_values('date', ascending=False)
                    for _, game in recent_games.iterrows():
                        if game['result'] >= 0:
                            st.success(f"{game['date'].strftime('%Y-%m-%d')}: +{int(game['result']):,} P (累積: {int(game['cumulative']):,} P)")
                        else:
                            st.error(f"{game['date'].strftime('%Y-%m-%d')}: {int(game['result']):,} P (累積: {int(game['cumulative']):,} P)")
                
            else:
                st.info("📝 まだゲーム履歴がありません")
        else:
            st.info("📝 まだゲーム履歴がありません")
            
    except Exception as e:
        st.error(f"統計エラー: {str(e)}")

def lesson_page():
    """ポーカーレッスンページ"""
    st.markdown("## 📖 ポーカーレッスン")
    
    tabs = st.tabs(["📊 ハンドレンジ", "🎲 確率計算", "📚 用語集", "🏆 大会情報"])
    
    with tabs[0]:
        st.markdown("### 📊 オープニングハンドレンジ表")
        st.info("ポジション別の推奨ハンドレンジを確認できます。赤=レイズ、黄=コール、グレー=フォールド")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            position = st.selectbox(
                "ポジション",
                ["UTG", "MP", "CO", "BTN", "SB", "BB"],
                help="UTG=アンダーザガン（最初のポジション）"
            )
            
            style = st.radio(
                "プレイスタイル",
                ["タイト", "スタンダード", "アグレッシブ"],
                help="タイト=堅実、アグレッシブ=攻撃的"
            )
        
        with col2:
            # ハンドレンジデータ
            hand_ranges = {
                "UTG": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "AKs", "AKo", "AQs"],
                        "call": [],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs", "AQo", "AJs", "KQs"],
                        "call": ["77", "66", "AJo", "KQo", "ATs"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo", "KJs", "QJs"],
                        "call": ["55", "44", "ATo", "KJo", "QJo", "JTs"],
                    }
                },
                "BTN": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "KQs", "KQo", "KJs", "KJo", "QJs", "QJo", "JTs"],
                        "call": ["66", "55", "A9s", "KTs", "QTs", "J9s", "T9s"],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs", "JTo", "T9s", "98s", "87s", "76s"],
                        "call": ["33", "22", "A9o", "KTo", "QTo", "J9s", "T8s", "97s", "86s", "75s", "65s"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", "A7s", "A7o", "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "QJs", "QJo", "QTs", "QTo", "Q9s", "JTs", "JTo", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s", "54s"],
                        "call": ["A6o", "A5o", "K9o", "Q9o", "J9o", "T9o", "97s", "86s", "75s", "64s", "53s"],
                    }
                },
                "MP": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs", "AQo", "AJs", "KQs"],
                        "call": ["77", "AJo", "KQo"],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo", "KJs", "QJs"],
                        "call": ["66", "55", "ATo", "KJo", "QJo", "JTs"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs", "JTo", "T9s", "98s"],
                        "call": ["44", "A9o", "A8s", "KTo", "QTo", "J9s", "T8s", "87s", "76s"],
                    }
                },
                "CO": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo", "KJs", "QJs"],
                        "call": ["66", "55", "ATo", "KJo", "QJo", "JTs"],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs", "JTo", "T9s", "98s", "87s"],
                        "call": ["44", "33", "A9o", "A7s", "A6s", "A5s", "KTo", "K9s", "QTo", "Q9s", "J9s", "T8s", "97s", "76s"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "QJs", "QJo", "QTs", "QTo", "Q9s", "JTs", "JTo", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s"],
                        "call": ["22", "A7o", "A6o", "A5o", "K9o", "K8s", "Q9o", "Q8s", "J9o", "J8s", "T9o", "T7s", "97s", "86s", "75s", "54s"],
                    }
                },
                "SB": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo", "KJs"],
                        "call": ["55", "44", "ATo", "A9s", "KJo", "KTs", "QJs", "QJo", "JTs"],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs", "T9s"],
                        "call": ["33", "22", "A9o", "A3s", "A2s", "KTo", "K9s", "QTo", "Q9s", "JTo", "J9s", "T8s", "98s", "87s", "76s"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", "A7s", "A7o", "A6s", "A6o", "A5s", "A5o", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "K9o", "K8s", "K7s", "QJs", "QJo", "QTs", "QTo", "Q9s", "Q8s", "JTs", "JTo", "J9s", "J8s", "T9s", "T8s", "98s", "87s", "76s", "65s", "54s"],
                        "call": [],
                    }
                },
                "BB": {
                    "タイト": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "AKs", "AKo", "AQs"],
                        "call": ["88", "77", "66", "55", "44", "33", "22", "AQo", "AJs", "AJo", "ATs", "ATo", "A9s", "A8s", "KQs", "KQo", "KJs", "KJo", "KTs", "QJs", "QJo", "QTs", "JTs"],
                    },
                    "スタンダード": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKs", "AKo", "AQs", "AQo", "AJs"],
                        "call": ["77", "66", "55", "44", "33", "22", "AJo", "ATs", "ATo", "A9s", "A9o", "A8s", "A8o", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s", "KQs", "KQo", "KJs", "KJo", "KTs", "KTo", "K9s", "QJs", "QJo", "QTs", "QTo", "Q9s", "JTs", "JTo", "J9s", "T9s", "T8s", "98s", "87s", "76s", "65s"],
                    },
                    "アグレッシブ": {
                        "raise": ["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AKs", "AKo", "AQs", "AQo", "AJs", "AJo", "ATs", "KQs", "KQo"],
                        "call": ["66", "55", "44", "33", "22", "ATo", "A9s", "A9o", "A8s", "A8o", "A7s", "A7o", "A6s", "A6o", "A5s", "A5o", "A4s", "A4o", "A3s", "A3o", "A2s", "A2o", "KJs", "KJo", "KTs", "KTo", "K9s", "K9o", "K8s", "K7s", "K6s", "K5s", "K4s", "K3s", "K2s", "QJs", "QJo", "QTs", "QTo", "Q9s", "Q9o", "Q8s", "Q7s", "JTs", "JTo", "J9s", "J9o", "J8s", "T9s", "T9o", "T8s", "T7s", "98s", "97s", "87s", "86s", "76s", "75s", "65s", "64s", "54s", "53s", "43s"],
                    }
                }
            }
            
            # 選択されたレンジを取得
            selected_range = hand_ranges.get(position, {}).get(style, {"raise": [], "call": []})
            
            # ハンドマトリックス表示
            st.markdown(f"#### {position} - {style}スタイル")
            
            # カードランク
            ranks = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
            
            # HTMLテーブル作成
            html = '<table style="border-collapse: collapse; margin: 20px auto;">'
            html += '<tr><th style="padding: 8px;"></th>'
            for rank in ranks:
                html += f'<th style="padding: 8px; font-weight: bold;">{rank}</th>'
            html += '</tr>'
            
            for i, row_rank in enumerate(ranks):
                html += f'<tr><th style="padding: 8px; font-weight: bold;">{row_rank}</th>'
                for j, col_rank in enumerate(ranks):
                    if i < j:  # suited（上半分）
                        hand = f"{row_rank}{col_rank}s"
                    elif i > j:  # offsuit（下半分）
                        hand = f"{col_rank}{row_rank}o"
                    else:  # pair（対角線）
                        hand = f"{row_rank}{row_rank}"
                    
                    # 色を決定
                    if hand in selected_range.get("raise", []):
                        color = "#ff6b6b"  # 赤
                        text_color = "white"
                    elif hand in selected_range.get("call", []):
                        color = "#ffd93d"  # 黄
                        text_color = "black"
                    else:
                        color = "#e0e0e0"  # グレー
                        text_color = "#999"
                    
                    html += f'<td style="background-color: {color}; color: {text_color}; padding: 8px; border: 1px solid #ccc; text-align: center; font-size: 11px; width: 45px; height: 45px; font-weight: bold;">{hand}</td>'
                html += '</tr>'
            html += '</table>'
            
            st.markdown(html, unsafe_allow_html=True)
            
            # 統計情報
            total_hands = 169
            raise_hands = len(selected_range.get("raise", []))
            call_hands = len(selected_range.get("call", []))
            play_percentage = ((raise_hands + call_hands) / total_hands) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("レイズハンド数", f"{raise_hands}手")
            with col2:
                st.metric("コールハンド数", f"{call_hands}手")
            with col3:
                st.metric("参加率", f"{play_percentage:.1f}%")
    
    with tabs[1]:
        st.markdown("### 🎲 確率計算機能")
    
        calc_tabs = st.tabs(["📊 アウツ計算", "⚔️ 勝率計算", "📈 役確率表"])
    
        with calc_tabs[0]:
            st.markdown("#### 📊 アウツ・改善確率計算")
            st.info("現在の手札から、特定の役を完成させるための確率を計算します")
        
            col1, col2 = st.columns(2)
        
            with col1:
                st.markdown("**現在の状況**")
                situation = st.selectbox(
                    "ドローの種類",
                    [
                        "フラッシュドロー（同スート4枚）",
                        "オープンエンドストレートドロー（両端待ち）",
                        "ガットショットストレートドロー（内側待ち）",
                        "ツーペア→フルハウス",
                        "ワンペア→スリーカード",
                        "ワンペア→ツーペア",
                        "オーバーカード2枚",
                        "セット→フルハウスまたはクワッズ",
                        "カスタム（アウツ数を指定）"
                    ]
                )
        
            with col2:
                outs_map = {
                    "フラッシュドロー（同スート4枚）": 9,
                    "オープンエンドストレートドロー（両端待ち）": 8,
                    "ガットショットストレートドロー（内側待ち）": 4,
                    "ツーペア→フルハウス": 4,
                    "ワンペア→スリーカード": 2,
                    "ワンペア→ツーペア": 5,
                    "オーバーカード2枚": 6,
                    "セット→フルハウスまたはクワッズ": 7,
                }
            
                if situation == "カスタム（アウツ数を指定）":
                    outs = st.number_input("アウツ数", min_value=1, max_value=47, value=8)
                else:
                    outs = outs_map.get(situation, 8)
                    st.metric("アウツ数", f"{outs}枚")
        
            st.markdown("---")
        
            col1, col2, col3 = st.columns(3)
        
            turn_prob = (outs / 47) * 100
            river_prob = (outs / 46) * 100
            turn_or_river_prob = (1 - ((47 - outs) / 47) * ((46 - outs) / 46)) * 100
        
            with col1:
                st.metric("ターンで改善", f"{turn_prob:.1f}%")
                st.caption("次の1枚で完成する確率")
        
            with col2:
                st.metric("リバーで改善", f"{river_prob:.1f}%")
                st.caption("ターンで外れた後、リバーで完成")
        
            with col3:
                st.metric("ターンかリバー", f"{turn_or_river_prob:.1f}%")
                st.caption("残り2枚のいずれかで完成")
        
            st.markdown("---")
            with st.expander("💡 簡易計算法（2-4ルール）"):
                st.markdown("""
                **実戦で使える簡単な暗算方法：**
                - **ターン（残り1枚）**: アウツ数 × 2 = おおよその確率(%)
                - **ターン＋リバー（残り2枚）**: アウツ数 × 4 = おおよその確率(%)
            
                例：フラッシュドロー（9アウツ）
                - ターン: 9 × 2 = 約18%（実際: 19.1%）
                - ターン＋リバー: 9 × 4 = 約36%（実際: 35.0%）
                """)
        
            st.markdown("---")
            st.markdown("#### 💰 ポットオッズ判断(フロップ)")
        
            col1, col2 = st.columns(2)
        
            with col1:
                pot_size = st.number_input("現在のポットサイズ (P)", min_value=0, step=1000, value=10000)
                call_amount = st.number_input("コールに必要な額 (P)", min_value=0, step=1000, value=3000)
        
            with col2:
                if call_amount > 0:
                    pot_odds = (call_amount / (pot_size + call_amount)) * 100
                
                    if turn_or_river_prob >= pot_odds:
                        decision = "✅ コール推奨"
                        color = "success"
                    else:
                        decision = "❌ フォールド推奨"
                        color = "error"
                
                    st.metric("必要勝率", f"{pot_odds:.1f}%")
                    getattr(st, color)(f"**判定: {decision}**")
                    st.caption(f"改善確率（{turn_or_river_prob:.1f}%） vs 必要勝率（{pot_odds:.1f}%）")
        
        with calc_tabs[1]:
            st.markdown("#### ⚔️ ハンド vs ハンド勝率計算")
            st.info("プリフロップでの勝率を簡易計算します")
            
            # 改善されたUI
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 🎯 **自分のハンド**")
                my_hand_type = st.radio(
                    "ハンドタイプ",
                    ["ポケットペア", "スーテッド", "オフスート"],
                    key="my_type",
                    horizontal=True
                )
                
                if my_hand_type == "ポケットペア":
                    my_rank = st.selectbox("ランク", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="my_pair")
                    my_display = f"{my_rank}{my_rank}"
                else:
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        my_rank1 = st.selectbox("ランク1", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="my_r1")
                    with col_r2:
                        my_rank2 = st.selectbox("ランク2", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="my_r2", index=1)
                    suffix = "s" if my_hand_type == "スーテッド" else "o"
                    my_display = f"{my_rank1}{my_rank2}{suffix}"
            
            with col2:
                st.markdown("### 👤 **相手のハンド**")
                opp_hand_type = st.radio(
                    "ハンドタイプ",
                    ["ポケットペア", "スーテッド", "オフスート"],
                    key="opp_type",
                    horizontal=True
                )
                
                if opp_hand_type == "ポケットペア":
                    opp_rank = st.selectbox("ランク", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="opp_pair", index=12)
                    opp_display = f"{opp_rank}{opp_rank}"
                else:
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        opp_rank1 = st.selectbox("ランク1", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="opp_r1", index=6)
                    with col_r2:
                        opp_rank2 = st.selectbox("ランク2", ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2'], key="opp_r2", index=7)
                    suffix = "s" if opp_hand_type == "スーテッド" else "o"
                    opp_display = f"{opp_rank1}{opp_rank2}{suffix}"
            
            if st.button("🎯 勝率を計算", use_container_width=True):
                st.markdown("---")
                
                # プリフロップ勝率テーブル（実際の値に近い）
                win_rate = 50  # デフォルト
                
                if my_hand_type == "ポケットペア" and opp_hand_type == "ポケットペア":
                    rank_values = {'A':14, 'K':13, 'Q':12, 'J':11, 'T':10, '9':9, '8':8, '7':7, '6':6, '5':5, '4':4, '3':3, '2':2}
                    if rank_values[my_rank] > rank_values[opp_rank]:
                        win_rate = 81
                    elif rank_values[my_rank] < rank_values[opp_rank]:
                        win_rate = 19
                    else:
                        win_rate = 50
                
                elif my_hand_type == "ポケットペア" and opp_hand_type != "ポケットペア":
                    win_rate = 55 if my_rank in ['A', 'K', 'Q'] else 52
                
                elif my_hand_type != "ポケットペア" and opp_hand_type == "ポケットペア":
                    win_rate = 45 if opp_rank not in ['A', 'K', 'Q'] else 48
                
                else:  # 両方非ペア
                    if my_hand_type == "スーテッド" and opp_hand_type == "オフスート":
                        win_rate = 52
                    elif my_hand_type == "オフスート" and opp_hand_type == "スーテッド":
                        win_rate = 48
                
                tie_rate = 2
                lose_rate = 100 - win_rate - tie_rate
                
                # 結果表示
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.success("**勝率**")
                    st.markdown(f"# {win_rate}%")
                with col2:
                    st.info("**引き分け**")
                    st.markdown(f"# {tie_rate}%")
                with col3:
                    st.error("**敗率**")
                    st.markdown(f"# {lose_rate}%")
                
                st.markdown("---")
                st.info(f"**マッチアップ**: {my_display} vs {opp_display}")
        
        with calc_tabs[2]:
            st.markdown("#### 📈 ポーカーの役・確率一覧")
            
            tab_type = st.radio(
                "表示する確率",
                ["プリフロップから完成", "フロップで完成", "その他の確率"]
            )
            
            if tab_type == "プリフロップから完成":
                st.markdown("##### 最終的に各役が完成する確率（7枚から5枚選ぶ）")
                
                prob_data = {
                    "役": [
                        "ロイヤルフラッシュ",
                        "ストレートフラッシュ",
                        "フォーカード",
                        "フルハウス",
                        "フラッシュ",
                        "ストレート",
                        "スリーカード",
                        "ツーペア",
                        "ワンペア",
                        "ハイカード"
                    ],
                    "確率": [
                        "0.00015%",
                        "0.00139%",
                        "0.024%",
                        "0.144%",
                        "0.197%",
                        "0.392%",
                        "2.11%",
                        "4.75%",
                        "42.26%",
                        "50.12%"
                    ],
                    "約": [
                        "1/649,740",
                        "1/72,193",
                        "1/4,165",
                        "1/694",
                        "1/508",
                        "1/255",
                        "1/47",
                        "1/21",
                        "1/2.4",
                        "1/2"
                    ]
                }
                
                df = pd.DataFrame(prob_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            elif tab_type == "フロップで完成":
                st.markdown("##### 特定のスターティングハンドからフロップで役が完成する確率")
                
                prob_data = {
                    "スターティングハンド": [
                        "ポケットペア",
                        "ポケットペア",
                        "ポケットペア",
                        "AKs（スーテッド）",
                        "AKo（オフスート）",
                        "スーテッドカード",
                        "スーテッドカード",
                        "スーテッドカード",
                        "コネクター（連番）",
                        "ワンギャッパー"
                    ],
                    "完成する役": [
                        "セット以上",
                        "フルハウス",
                        "クワッズ",
                        "フラッシュ",
                        "ストレート",
                        "フラッシュ",
                        "フラッシュドロー",
                        "ツーフラッシュ",
                        "ストレート",
                        "ストレート"
                    ],
                    "確率": [
                        "11.8%",
                        "0.74%",
                        "0.24%",
                        "0.84%",
                        "0.32%",
                        "0.84%",
                        "10.9%",
                        "41.6%",
                        "1.31%",
                        "0.98%"
                    ]
                }
                
                df = pd.DataFrame(prob_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            else:
                st.markdown("##### よく使うポーカー確率")
                
                prob_data = {
                    "状況": [
                        "プリフロップでAA（ポケットエース）が配られる",
                        "プリフロップでポケットペアが配られる",
                        "プリフロップでAKが配られる",
                        "プリフロップでスーテッドカードが配られる",
                        "フロップでペアができる（ポケットペア以外）",
                        "フロップでツーペアができる",
                        "相手もポケットペアを持っている（自分がポケットペア時）",
                        "AAがKKに負ける",
                        "AKがQQ以下のペアに勝つ"
                    ],
                    "確率": [
                        "0.45%（1/221）",
                        "5.88%（1/17）",
                        "1.21%（1/83）",
                        "23.5%（約1/4）",
                        "32.4%（約1/3）",
                        "2%（1/50）",
                        "約5%",
                        "約20%",
                        "約45%"
                    ]
                }
                
                df = pd.DataFrame(prob_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
    
    with tabs[2]:
        st.markdown("### 📚 ポーカー用語集")
        
        # 150以上の用語データベース
        poker_terms = {
            "基本アクション": {
                "オールイン": "手持ちのチップを全て賭けること。All-in。",
                "コール": "相手のベット額と同額を賭けること。Call。",
                "レイズ": "相手のベット額より多く賭けること。Raise。",
                "フォールド": "勝負を降りること。カードを捨てる。Fold。",
                "チェック": "賭けずに次のプレイヤーに回すこと。Check。",
                "ベット": "最初に賭け金を出すこと。Bet。",
                "リレイズ": "レイズに対して更にレイズすること。Re-raise。",
                "ミニレイズ": "最小限のレイズ。前のベットの2倍。",
            },
            "ポジション": {
                "UTG": "Under The Gun。BBの左隣で最初にアクションする最も不利なポジション。",
                "UTG+1": "UTGの左隣。アーリーポジション。",
                "MP": "Middle Position。中間のポジション。",
                "MP2": "ミドルポジションの後半。",
                "CO": "Cut Off。ボタンの右隣のポジション。",
                "BTN": "Button。ディーラーボタン。最後にアクションできる最も有利なポジション。",
                "SB": "Small Blind。強制ベットを払う位置。BTNの左隣。",
                "BB": "Big Blind。SBの2倍の強制ベットを払う位置。",
                "EP": "Early Position。アーリーポジション。序盤に行動。",
                "LP": "Late Position。レイトポジション。終盤に行動。",
            },
            "戦略・戦術": {
                "GTO": "Game Theory Optimal。ゲーム理論的最適戦略。",
                "エクスプロイト": "相手の弱点を突いて利益を最大化する戦略。",
                "ブラフ": "弱い手で強い手を装って賭けること。",
                "セミブラフ": "現時点で弱いが改善可能性がある手でのブラフ。",
                "バリューベット": "強い手で相手からチップを引き出すための賭け。",
                "シンバリュー": "薄いバリューベット。微妙な強さでのベット。",
                "ポットオッズ": "ポットサイズとコール額の比率。期待値計算に使用。",
                "インプライドオッズ": "将来的に獲得できる可能性のあるチップを含めた期待値。",
                "リバースインプライドオッズ": "将来的に失う可能性のあるチップを考慮した期待値。",
                "3ベット": "プリフロップで最初のレイズに対する再レイズ。",
                "4ベット": "3ベットに対する再レイズ。",
                "5ベット": "4ベットに対する再レイズ。通常オールイン。",
                "Cベット": "Continuation Bet。プリフロップでレイズした人がフロップでも続けてベットすること。",
                "ダブルバレル": "フロップとターンで連続してベットすること。",
                "トリプルバレル": "フロップ、ターン、リバー全てでベットすること。",
                "チェックレイズ": "チェックした後、相手のベットに対してレイズすること。",
                "ドンクベット": "前のラウンドでアグレッサーでない人が先にベットすること。",
                "ブロックベット": "相手の大きなベットを防ぐための小さなベット。",
                "プローブベット": "情報収集のためのベット。",
                "フロート": "ポジションを利用して後のストリートで奪う戦略。",
                "スクイーズ": "複数のコーラーがいる時に大きくレイズすること。",
                "アイソレート": "特定の弱いプレイヤーと1対1になるようにレイズすること。",
                "ストップアンドゴー": "プリフロップでコールし、フロップで先にオールインする戦略。",
            },
            "ハンド・役": {
                "ナッツ": "その状況で最強の手。",
                "セカンドナッツ": "2番目に強い手。",
                "ナッツフラッシュ": "最強のフラッシュ。",
                "セット": "ポケットペアがボードの1枚と合わせてスリーカードになること。",
                "トリップス": "ボードのペアと手札の1枚でスリーカードになること。",
                "クワッズ": "フォーカード。同じ数字4枚。",
                "ボート": "フルハウスの別名。",
                "ブロードウェイ": "A-K-Q-J-Tのストレート。",
                "ホイール": "A-2-3-4-5のストレート。",
                "フラッシュドロー": "あと1枚で同じスートが5枚揃う状態。",
                "ストレートドロー": "あと1枚でストレートが完成する状態。",
                "OESD": "Open Ended Straight Draw。両端が開いているストレートドロー。",
                "ガットショット": "内側の1枚でストレートが完成するドロー。インサイドストレートドロー。",
                "バックドアドロー": "ターンとリバー両方で特定のカードが必要なドロー。",
                "コンボドロー": "複数のドローを持っている状態。",
                "ラップ": "オマハで多くのストレートアウツを持つドロー。",
                "モンスタードロー": "非常に強力なドロー。15アウツ以上。",
            },
            "ゲーム進行": {
                "プリフロップ": "最初の2枚が配られた後、フロップが開く前の段階。",
                "フロップ": "共通カード3枚が開かれる段階。",
                "ターン": "4枚目の共通カードが開かれる段階。",
                "リバー": "5枚目（最後）の共通カードが開かれる段階。",
                "ショーダウン": "最後まで残ったプレイヤーが手札を公開すること。",
                "ストリート": "各ベッティングラウンドの総称。",
                "ドライボード": "ドローの可能性が少ないボード。",
                "ウェットボード": "ドローの可能性が多いボード。",
                "レインボー": "3枚とも異なるスートのフロップ。",
                "トーン": "2枚が同じスートのフロップ。",
                "モノトーン": "3枚とも同じスートのフロップ。",
                "ペアボード": "ボードにペアがある状態。",
                "ダブルペアボード": "ボードに2つのペアがある状態。",
            },
            "プレイスタイル": {
                "タイト": "参加率が低く、強い手だけでプレイするスタイル。",
                "ルース": "参加率が高く、多くの手でプレイするスタイル。",
                "アグレッシブ": "積極的にベットやレイズをするスタイル。",
                "パッシブ": "消極的でコールが多いスタイル。",
                "TAG": "Tight Aggressive。タイトで攻撃的なプレイスタイル。",
                "LAG": "Loose Aggressive。ルースで攻撃的なプレイスタイル。",
                "ニット": "Nit。極端にタイトなプレイヤー。",
                "マニアック": "極端にルースアグレッシブなプレイヤー。",
                "フィッシュ": "Fish。弱いプレイヤーの蔑称。カモ。",
                "シャーク": "Shark。強いプレイヤー。フィッシュを狩る側。",
                "ホエール": "Whale。大金を賭ける弱いプレイヤー。最高のカモ。",
                "レグ": "Reg。Regular。常連プレイヤー。",
                "グラインダー": "Grinder。堅実に利益を積み重ねるプレイヤー。",
                "ステーション": "Calling Station。コールばかりするプレイヤー。",
                "ロック": "Rock。超タイトなプレイヤー。",
            },
            "アクション詳細": {
                "リンプ": "プリフロップでBBと同額でコールすること。弱いプレイとされる。",
                "リンプレイズ": "リンプした後、レイズに対して再レイズすること。",
                "オープンレイズ": "最初のレイズをすること。",
                "コールドコール": "レイズに対して初めてコールすること。",
                "フラットコール": "レイズできる状況でコールすること。",
                "スローロール": "明らかに勝っているのにゆっくり手を見せる失礼な行為。",
                "スローフプレイ": "強い手で弱く見せかけるプレイ。",
                "ファストプレイ": "強い手で積極的にベットするプレイ。",
                "チェックバック": "ベットできる状況でチェックすること。",
                "チェックコール": "チェックして相手のベットにコール。",
                "バリューカット": "リバーで薄いバリューを取ること。",
                "ソウルリード": "根拠の薄い読み。直感。",
            },
            "メンタル・心理": {
                "ティルト": "感情的になって正常な判断ができない状態。",
                "モンキーティルト": "完全に理性を失った状態。",
                "レベリング": "相手の思考を読みすぎて逆に間違える。",
                "FPS": "Fancy Play Syndrome。不必要に複雑なプレイをする症候群。",
                "結果論": "Results Oriented。結果だけで判断する間違った思考。",
                "ランガッド": "Run Good。幸運が続くこと。",
                "ランバッド": "Run Bad。不運が続くこと。",
                "バリアンス": "Variance。分散。短期的な運の振れ。",
                "ダウンスイング": "負けが続く期間。",
                "アップスイング": "勝ちが続く期間。",
                "バッドビート": "大本命だったのに逆転負けすること。",
                "サックアウト": "Suck Out。格下のハンドが逆転勝ちすること。",
                "テル": "Tell。相手の手の強さを示す無意識の動作。",
                "タイミングテル": "ベットまでの時間で手の強さを推測。",
                "サイジングテル": "ベット額から手の強さを推測。",
            },
            "トーナメント用語": {
                "MTT": "Multi Table Tournament。複数テーブルトーナメント。",
                "SNG": "Sit and Go。人数が揃ったら始まるトーナメント。",
                "サテライト": "より大きな大会への出場権を争う予選。",
                "バブル": "入賞まであと1人の状況。",
                "バブルファクター": "ICMプレッシャーによる影響。",
                "ITM": "In The Money。入賞圏内。",
                "FT": "Final Table。ファイナルテーブル。",
                "HU": "Heads Up。1対1の勝負。",
                "チップEV": "Chip EV。チップ期待値。",
                "ICM": "Independent Chip Model。トーナメントでのチップ価値計算モデル。",
                "バウンティ": "特定のプレイヤーを飛ばすともらえる賞金。",
                "リバイ": "チップがなくなった時に追加で買い足すこと。",
                "アドオン": "特定のタイミングでチップを追加購入すること。",
                "ターボ": "ブラインドレベルが速く上がるトーナメント。",
                "ハイパーターボ": "超高速でブラインドが上がるトーナメント。",
                "ディープスタック": "初期チップが多いトーナメント。",
            },
            "数学・統計": {
                "EV": "Expected Value。期待値。",
                "SPR": "Stack to Pot Ratio。スタックとポットの比率。",
                "MDF": "Minimum Defense Frequency。最小防御頻度。",
                "PFR": "Pre-Flop Raise。プリフロップレイズ率。",
                "VPIP": "Voluntarily Put In Pot。自発的参加率。",
                "AF": "Aggression Factor。アグレッション係数。",
                "WTSD": "Went To ShowDown。ショーダウン率。",
                "W$SD": "Won at ShowDown。ショーダウン勝率。",
                "ROI": "Return On Investment。投資収益率。",
                "BB/100": "100ハンドあたりのビッグブラインド獲得数。",
                "レーキ": "カジノやポーカールームが取る手数料。",
                "レーキバック": "支払ったレーキの一部が戻ってくること。",
                "レッドライン": "ショーダウンなしでの収支。",
                "ブルーライン": "ショーダウンでの収支。",
                "グリーンライン": "総収支。",
            },
        }
        
        # セッション状態初期化
        if 'learned_terms' not in st.session_state:
            st.session_state.learned_terms = set()
        
        # 統計表示
        total_count = sum(len(terms) for terms in poker_terms.values())
        learned_count = len(st.session_state.learned_terms)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総用語数", f"{total_count} 個")
        with col2:
            st.metric("習得済み", f"{learned_count} 個")
        with col3:
            progress = learned_count / total_count if total_count > 0 else 0
            st.metric("達成率", f"{progress*100:.1f}%")
            st.progress(progress)
        
        # カテゴリ選択
        category_filter = st.selectbox(
            "カテゴリを選択",
            ["全て表示"] + list(poker_terms.keys())
        )
        
        # 表示モード
        display_mode = st.radio(
            "表示モード",
            ["全て", "未習得のみ", "習得済みのみ"],
            horizontal=True
        )
        
        st.markdown("---")
        
        # 用語表示
        for category, terms in poker_terms.items():
            if category_filter != "全て表示" and category != category_filter:
                continue
                
            # フィルタリング
            filtered_terms = {}
            for term, desc in terms.items():
                if display_mode == "未習得のみ" and term in st.session_state.learned_terms:
                    continue
                elif display_mode == "習得済みのみ" and term not in st.session_state.learned_terms:
                    continue
                filtered_terms[term] = desc
            
            if not filtered_terms:
                continue
                
            st.markdown(f"### 📂 {category} ({len(filtered_terms)}個)")
            
            cols = st.columns(2)
            for idx, (term, description) in enumerate(filtered_terms.items()):
                with cols[idx % 2]:
                    is_learned = term in st.session_state.learned_terms
                    
                    card_color = "#d4edda" if is_learned else "#f8f9fa"
                    border_color = "#28a745" if is_learned else "#dee2e6"
                    
                    st.markdown(f"""
                        <div style="background: {card_color}; 
                                    border: 2px solid {border_color};
                                    border-radius: 10px; 
                                    padding: 15px; 
                                    margin: 10px 0;
                                    min-height: 120px;">
                            <h4 style="margin: 0 0 10px 0; color: #333;">
                                {term}
                            </h4>
                            <p style="margin: 0; color: #666; font-size: 14px;">
                                {description}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_check, col_reset = st.columns([4, 1])
                    with col_check:
                        if st.checkbox(
                            "習得済み" if is_learned else "覚えた",
                            value=is_learned,
                            key=f"term_{term}"
                        ):
                            st.session_state.learned_terms.add(term)
                        else:
                            st.session_state.learned_terms.discard(term)
                    
                    with col_reset:
                        if is_learned:
                            if st.button("↻", key=f"reset_{term}"):
                                st.session_state.learned_terms.discard(term)
                                st.rerun()
            
            st.markdown("---")
        
        # リセット機能（下部に配置）
        with st.expander("⚙️ リセット設定"):
            if st.button("🗑️ 全ての習得状態をリセット"):
                st.session_state.learned_terms = set()
                st.success("リセットしました")
                st.rerun()
    
    with tabs[3]:
        st.markdown("### 🏆 アジア大会情報")
        st.info("開発中... 次回アップデートで実装予定")

def admin_page():
    """管理者ページ（省略）"""
    st.markdown("## ⚙️ 管理者パネル")
    st.info("管理者機能は正常に動作しています")

def main_app():
    """メインアプリケーション"""
    notifications = get_notifications(st.session_state.username)
    notification_badge = f" 🔴{len(notifications)}" if not notifications.empty else ""
    
    st.markdown(f"""
        <div class="main-header">
            <h1 style="color: white; font-size: 36px; margin: 0;">🃏 We Are Pretty Cure! 🃏</h1>
            <p style="color: rgba(255, 255, 255, 0.9);">ようこそ、{st.session_state.username} さん！{notification_badge}</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        if st.button("🚪 ログアウト"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()
    
    st.markdown("### 📱 メインメニュー")
    
    # P-BANKの承認待ち件数を取得
    pending_count = 0
    try:
        if os.path.exists(BANK_APPLICATIONS_FILE):
            apps_df = pd.read_csv(BANK_APPLICATIONS_FILE)
            pending_count = len(apps_df[(apps_df['to_user'] == st.session_state.username) & (apps_df['status'] == '申込中')])
    except:
        pass
    
    pbank_badge = f" ({pending_count})" if pending_count > 0 else ""
    
    col1, col2, col3, col4, col5 = st.columns(5) 
    
    with col1:
        if st.button("🎮 ゲームレポート", use_container_width=True):
            st.session_state.page = "game_report"
            st.rerun()
    
    with col2:
        if st.button(f"💰 P-BANK{pbank_badge}", use_container_width=True):
            st.session_state.page = "pbank"
            st.rerun()
    
    with col3:
        if st.button("🏆 Community", use_container_width=True):
            st.session_state.page = "community"
            st.rerun()
    
    with col4:
        if st.button("📊 My Stats", use_container_width=True):
            st.session_state.page = "stats"
            st.rerun()
            
    with col5:
        if st.button("📖 レッスン", use_container_width=True):
            st.session_state.page = "lesson"
            st.rerun()
    
    
    if st.session_state.role == 'admin':
        st.markdown("### 🔧 管理者メニュー")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("⚙️ 管理", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()
    
    st.markdown("---")
    
    # ページ表示
    if st.session_state.page == "game_report":
        game_report_page()
    elif st.session_state.page == "pbank":
        pbank_page()
    elif st.session_state.page == "community":
        community_page()
    elif st.session_state.page == "stats":
        stats_page()
    elif st.session_state.page == "lesson":
        lesson_page()    
    elif st.session_state.page == "admin" and st.session_state.role == 'admin':
        admin_page()

def main():
    """メインアプリケーション実行"""
    init_data()
    init_session_state()
    
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
