import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')
sns.set_theme(style='whitegrid', palette='muted')
plt.rcParams['figure.dpi'] = 100

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Brasil Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 16px 20px;
        border-left: 4px solid #4c72b0;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    orders_df             = pd.read_csv('orders_dataset.csv')
    order_items_df        = pd.read_csv('order_items_dataset.csv')
    order_payments_df     = pd.read_csv('order_payments_dataset.csv')
    order_reviews_df      = pd.read_csv('order_reviews_dataset.csv')
    products_df           = pd.read_csv('products_dataset.csv')
    customers_df          = pd.read_csv('customers_dataset.csv')
    category_df           = pd.read_csv('product_category_name_translation.csv')

    date_cols = [
        'order_purchase_timestamp', 'order_approved_at',
        'order_delivered_carrier_date', 'order_delivered_customer_date',
        'order_estimated_delivery_date',
    ]
    for col in date_cols:
        orders_df[col] = pd.to_datetime(orders_df[col])
    order_reviews_df['review_creation_date'] = pd.to_datetime(
        order_reviews_df['review_creation_date'])

    return (orders_df, order_items_df, order_payments_df,
            order_reviews_df, products_df, customers_df, category_df)


(orders_df, order_items_df, order_payments_df,
 order_reviews_df, products_df, customers_df, category_df) = load_data()


# ─────────────────────────────────────────────
# BASE TABLE
# ─────────────────────────────────────────────
@st.cache_data
def build_base():
    orders_clean = orders_df[orders_df['order_status'] == 'delivered'].copy()

    order_value = (
        order_items_df.groupby('order_id')['price']
        .sum().reset_index()
        .rename(columns={'price': 'order_value'})
    )

    base = (
        orders_clean
        .merge(order_value, on='order_id', how='inner')
        .merge(customers_df[['customer_id', 'customer_unique_id',
                              'customer_state', 'customer_city']],
               on='customer_id', how='left')
        .merge(order_reviews_df[['order_id', 'review_score']],
               on='order_id', how='left')
    )
    base['year']       = base['order_purchase_timestamp'].dt.year
    base['year_month'] = base['order_purchase_timestamp'].dt.to_period('M')
    return base

base = build_base()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.title("🛒 Dashboard")
    st.caption("E-Commerce Brasil · 2016–2018")
    st.divider()

    years = sorted(base['year'].dropna().unique().astype(int))
    year_filter = st.multiselect(
        "Filter Tahun", options=years, default=years
    )

    st.divider()
    menu = st.radio(
        "Navigasi",
        ["Overview", "Revenue & Kategori",
         "Pengiriman & Ulasan", "Pembayaran",
         "Analisis Lanjutan"],
        label_visibility="collapsed"
    )

base_f = base[base['year'].isin(year_filter)]


# ─────────────────────────────────────────────
# ① OVERVIEW
# ─────────────────────────────────────────────
if menu == "Overview":
    st.title("Overview")
    st.caption(f"Menampilkan data tahun: {', '.join(map(str, year_filter))}")
    st.divider()

    total_orders   = base_f['order_id'].nunique()
    total_revenue  = base_f['order_value'].sum()
    avg_order      = base_f['order_value'].mean()
    avg_review     = base_f['review_score'].mean()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Order",        f"{total_orders:,}")
    c2.metric("Total Revenue",      f"R${total_revenue:,.0f}")
    c3.metric("Rata-rata Order",    f"R${avg_order:,.0f}")
    c4.metric("Avg Skor Ulasan",    f"{avg_review:.2f} ⭐")

    st.divider()

    # Monthly revenue trend
    monthly = (
        base_f.groupby('year_month')['order_value']
        .sum().reset_index()
        .rename(columns={'order_value': 'revenue'})
        .sort_values('year_month')
    )
    monthly['revenue_mom'] = monthly['revenue'].pct_change() * 100

    fig, ax1 = plt.subplots(figsize=(12, 4))
    ax1.fill_between(range(len(monthly)), monthly['revenue'] / 1_000,
                     alpha=0.2, color='#4c72b0')
    ax1.plot(range(len(monthly)), monthly['revenue'] / 1_000,
             color='#4c72b0', linewidth=2.5, marker='o', markersize=4)

    peak_idx = monthly['revenue'].idxmax()
    peak = monthly.loc[peak_idx]
    ax1.annotate(f"Puncak\nR${peak['revenue']/1000:,.0f}K",
                 xy=(peak_idx, peak['revenue'] / 1000),
                 xytext=(max(0, peak_idx - 2), peak['revenue'] / 1000 + 50),
                 arrowprops=dict(arrowstyle='->', color='#e63946'),
                 fontsize=9, color='#e63946', fontweight='bold')

    ax2 = ax1.twinx()
    mom_colors = ['#2a9d8f' if v >= 0 else '#e63946'
                  for v in monthly['revenue_mom'].fillna(0)]
    ax2.bar(range(len(monthly)), monthly['revenue_mom'].fillna(0),
            color=mom_colors, alpha=0.35, width=0.4)
    ax2.axhline(0, color='gray', linewidth=0.8, linestyle='--')
    ax2.set_ylabel('MoM Growth (%)', color='gray', fontsize=10)
    ax2.tick_params(axis='y', labelcolor='gray')

    tick_step = max(1, len(monthly) // 10)
    ax1.set_xticks(list(range(0, len(monthly), tick_step)))
    ax1.set_xticklabels(
        [str(monthly['year_month'].iloc[i]) for i in range(0, len(monthly), tick_step)],
        rotation=45, ha='right', fontsize=9)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}K'))
    ax1.set_ylabel('Revenue (Ribuan BRL)', fontsize=10)
    ax1.set_title('Tren Revenue Bulanan & MoM Growth', fontsize=12, fontweight='bold')
    sns.despine()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


# ─────────────────────────────────────────────
# ② REVENUE & KATEGORI
# ─────────────────────────────────────────────
elif menu == "Revenue & Kategori":
    st.title("Revenue & Kategori Produk")
    st.divider()

    cat_revenue = (
        base_f
        .merge(order_items_df[['order_id', 'product_id']], on='order_id', how='left')
        .merge(products_df[['product_id', 'product_category_name']], on='product_id', how='left')
        .merge(category_df, on='product_category_name', how='left')
        .groupby('product_category_name_english')['order_value']
        .sum().reset_index()
        .rename(columns={'order_value': 'total_revenue',
                         'product_category_name_english': 'category'})
        .sort_values('total_revenue', ascending=False)
    )

    n_top = st.slider("Tampilkan top N kategori", 5, 20, 10)
    top_n = cat_revenue.head(n_top)

    fig, ax = plt.subplots(figsize=(10, n_top * 0.55 + 1))
    colors = sns.color_palette('muted', n_top)
    bars = ax.barh(top_n['category'][::-1],
                   top_n['total_revenue'][::-1] / 1_000,
                   color=colors[::-1], edgecolor='white')
    for bar, val in zip(bars, top_n['total_revenue'][::-1] / 1_000):
        ax.text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                f'R${val:,.0f}K', va='center', fontsize=9, fontweight='bold')
    ax.set_xlabel('Total Revenue (Ribuan BRL)', fontsize=10)
    ax.set_title(f'Top {n_top} Kategori Produk — Total Revenue', fontsize=12, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}K'))
    sns.despine(ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    with st.expander("Lihat data lengkap"):
        st.dataframe(cat_revenue.reset_index(drop=True), use_container_width=True)


# ─────────────────────────────────────────────
# ③ PENGIRIMAN & ULASAN
# ─────────────────────────────────────────────
elif menu == "Pengiriman & Ulasan":
    st.title("Pengiriman & Ulasan Pelanggan")
    st.divider()

    delivery_df = base_f.dropna(subset=[
        'order_delivered_customer_date',
        'order_estimated_delivery_date',
        'review_score'
    ]).copy()

    delivery_df['delivery_days'] = (
        delivery_df['order_delivered_customer_date'] -
        delivery_df['order_purchase_timestamp']
    ).dt.days

    delivery_df['delay_days'] = (
        delivery_df['order_delivered_customer_date'] -
        delivery_df['order_estimated_delivery_date']
    ).dt.days

    delivery_df['status_kirim'] = delivery_df['delay_days'].apply(
        lambda x: 'Terlambat' if x > 0 else 'Tepat/Lebih Cepat'
    )

    delivery_score = (
        delivery_df.groupby('review_score')
        .agg(avg_days=('delivery_days', 'mean'),
             avg_delay=('delay_days', 'mean'),
             pct_terlambat=('status_kirim', lambda x: (x == 'Terlambat').mean() * 100))
        .reset_index()
    )

    score_colors = sns.color_palette('muted', 5)
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Avg delivery days
    bars = axes[0].bar(delivery_score['review_score'], delivery_score['avg_days'],
                       color=score_colors, edgecolor='white', width=0.6)
    for bar, val in zip(bars, delivery_score['avg_days']):
        axes[0].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.3, f'{val:.1f}d',
                     ha='center', fontsize=10, fontweight='bold')
    axes[0].set_title('Rata-rata Hari Pengiriman\nper Skor Ulasan', fontsize=11, fontweight='bold')
    axes[0].set_xlabel('Skor Ulasan')
    axes[0].set_ylabel('Rata-rata Hari')
    axes[0].set_xticks([1, 2, 3, 4, 5])
    axes[0].set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
    sns.despine(ax=axes[0])

    # Avg delay
    bars = axes[1].bar(delivery_score['review_score'], delivery_score['avg_delay'],
                       color=score_colors, edgecolor='white', width=0.6)
    axes[1].axhline(0, color='gray', linewidth=0.8, linestyle='--')
    for bar, val in zip(bars, delivery_score['avg_delay']):
        offset = 0.3 if val >= 0 else -1.8
        axes[1].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + offset, f'{val:.1f}d',
                     ha='center', fontsize=10, fontweight='bold')
    axes[1].set_title('Rata-rata Keterlambatan\n(Aktual − Estimasi)', fontsize=11, fontweight='bold')
    axes[1].set_xlabel('Skor Ulasan')
    axes[1].set_ylabel('Hari')
    axes[1].set_xticks([1, 2, 3, 4, 5])
    axes[1].set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
    sns.despine(ax=axes[1])

    # % terlambat
    bars = axes[2].bar(delivery_score['review_score'], delivery_score['pct_terlambat'],
                       color=score_colors, edgecolor='white', width=0.6)
    for bar, val in zip(bars, delivery_score['pct_terlambat']):
        axes[2].text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.5, f'{val:.1f}%',
                     ha='center', fontsize=10, fontweight='bold')
    axes[2].set_title('% Order Terlambat\nper Skor Ulasan', fontsize=11, fontweight='bold')
    axes[2].set_xlabel('Skor Ulasan')
    axes[2].set_ylabel('% Terlambat')
    axes[2].set_xticks([1, 2, 3, 4, 5])
    axes[2].set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
    sns.despine(ax=axes[2])

    plt.suptitle('Analisis Pengiriman & Korelasi dengan Ulasan Pelanggan',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Violin distribusi
    st.subheader("Distribusi Hari Pengiriman per Skor")
    fig2, ax = plt.subplots(figsize=(10, 5))
    sample = delivery_df.sample(min(5000, len(delivery_df)), random_state=42)
    parts = ax.violinplot(
        [sample[sample['review_score'] == s]['delivery_days'].dropna().values
         for s in [1, 2, 3, 4, 5]],
        positions=[1, 2, 3, 4, 5], showmedians=True)
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(score_colors[i])
        pc.set_alpha(0.7)
    ax.set_xticks([1, 2, 3, 4, 5])
    ax.set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
    ax.set_ylim(0, 100)
    ax.set_ylabel('Hari Pengiriman')
    ax.set_title('Distribusi Hari Pengiriman per Skor Ulasan',
                 fontsize=12, fontweight='bold')
    sns.despine(ax=ax)
    plt.tight_layout()
    st.pyplot(fig2)
    plt.close()


# ─────────────────────────────────────────────
# ④ PEMBAYARAN
# ─────────────────────────────────────────────
elif menu == "Pembayaran":
    st.title("Analisis Metode Pembayaran")
    st.divider()

    orders_in_filter = base_f['order_id'].unique()
    pay_f = order_payments_df[
        order_payments_df['order_id'].isin(orders_in_filter)
    ]

    payment_summary = (
        pay_f.groupby('payment_type')
        .agg(n_transactions=('order_id', 'count'),
             total_value=('payment_value', 'sum'),
             avg_value=('payment_value', 'mean'))
        .sort_values('n_transactions', ascending=False)
    )

    pay_labels = {
        'credit_card': 'Kartu Kredit',
        'boleto':      'Boleto',
        'voucher':     'Voucher',
        'debit_card':  'Kartu Debit',
    }
    payment_summary.index = [pay_labels.get(x, x) for x in payment_summary.index]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Transaksi",    f"{payment_summary['n_transactions'].sum():,}")
    c2.metric("Total Revenue",      f"R${payment_summary['total_value'].sum():,.0f}")
    c3.metric("Metode Terbanyak",   payment_summary['n_transactions'].idxmax())
    c4.metric("Avg Tertinggi",      f"R${payment_summary['avg_value'].max():,.0f}")

    st.divider()

    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    colors = sns.color_palette('muted', len(payment_summary))

    ax1 = axes[0]
    explode = [0.05] + [0] * (len(payment_summary) - 1)
    wedges, texts, autotexts = ax1.pie(
        payment_summary['n_transactions'],
        labels=payment_summary.index,
        autopct='%1.1f%%',
        colors=colors,
        explode=explode,
        startangle=140)
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')
    ax1.set_title('Distribusi Jumlah Transaksi\nper Metode Pembayaran',
                  fontsize=12, fontweight='bold')

    ax2 = axes[1]
    bars = ax2.bar(payment_summary.index, payment_summary['avg_value'],
                   color=colors, edgecolor='white', width=0.55)
    for bar, val in zip(bars, payment_summary['avg_value']):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1,
                 f'R${val:,.0f}', ha='center', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Rata-rata Nilai Transaksi (BRL)', fontsize=11)
    ax2.set_title('Rata-rata Nilai Transaksi\nper Metode Pembayaran',
                  fontsize=12, fontweight='bold')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
    sns.despine(ax=ax2)

    plt.suptitle('Analisis Metode Pembayaran Pelanggan',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    with st.expander("Lihat tabel detail"):
        st.dataframe(payment_summary, use_container_width=True)


# ─────────────────────────────────────────────
# ⑤ ANALISIS LANJUTAN
# ─────────────────────────────────────────────
elif menu == "Analisis Lanjutan":
    st.title("Analisis Lanjutan")
    tab1, tab2, tab3, tab4 = st.tabs([
        "Segmentasi Pelanggan",
        "Keterlambatan Kirim",
        "Repeat Purchase",
        "Geografis Revenue",
    ])

    # ── TAB 1: Segmentasi ──────────────────────
    with tab1:
        st.subheader("Segmentasi Pelanggan Berdasarkan Nilai Transaksi")

        customer_spending = (
            base_f.groupby('customer_unique_id')['order_value']
            .sum().reset_index()
            .rename(columns={'order_value': 'total_spending'})
        )
        q1 = customer_spending['total_spending'].quantile(0.33)
        q2 = customer_spending['total_spending'].quantile(0.66)
        customer_spending['segment'] = pd.cut(
            customer_spending['total_spending'],
            bins=[-np.inf, q1, q2, np.inf],
            labels=['Low Spender', 'Mid Spender', 'High Spender']
        )
        seg_summary = (
            customer_spending.groupby('segment', observed=True)
            .agg(jumlah_pelanggan=('customer_unique_id', 'count'),
                 avg_spending=('total_spending', 'mean'),
                 total_spending=('total_spending', 'sum'))
            .reset_index()
        )
        seg_summary['revenue_share_%'] = (
            seg_summary['total_spending'] / seg_summary['total_spending'].sum() * 100
        ).round(1)

        colors = sns.color_palette('muted', 3)
        fig, axes = plt.subplots(1, 3, figsize=(14, 5))

        bars = axes[0].bar(seg_summary['segment'], seg_summary['jumlah_pelanggan'],
                           color=colors, edgecolor='white', width=0.55)
        for bar, val in zip(bars, seg_summary['jumlah_pelanggan']):
            axes[0].text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 50, f'{val:,}',
                         ha='center', fontsize=10, fontweight='bold')
        axes[0].set_ylabel('Jumlah Pelanggan', fontsize=11)
        axes[0].set_title('Jumlah Pelanggan\nper Segmen', fontsize=12, fontweight='bold')
        sns.despine(ax=axes[0])

        bars = axes[1].bar(seg_summary['segment'], seg_summary['avg_spending'],
                           color=colors, edgecolor='white', width=0.55)
        for bar, val in zip(bars, seg_summary['avg_spending']):
            axes[1].text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 2, f'R${val:,.0f}',
                         ha='center', fontsize=10, fontweight='bold')
        axes[1].set_ylabel('Rata-rata Spending (BRL)', fontsize=11)
        axes[1].set_title('Rata-rata Spending\nper Segmen', fontsize=12, fontweight='bold')
        axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
        sns.despine(ax=axes[1])

        explode = [0.05, 0, 0]
        wedges, texts, autotexts = axes[2].pie(
            seg_summary['revenue_share_%'],
            labels=seg_summary['segment'],
            autopct='%1.1f%%',
            colors=colors, explode=explode, startangle=140)
        for at in autotexts:
            at.set_fontsize(10)
            at.set_fontweight('bold')
        axes[2].set_title('Kontribusi Revenue\nper Segmen', fontsize=12, fontweight='bold')

        plt.suptitle('Segmentasi Pelanggan Berdasarkan Nilai Transaksi',
                     fontsize=13, fontweight='bold', y=1.02)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── TAB 2: Keterlambatan ───────────────────
    with tab2:
        st.subheader("Keterlambatan Pengiriman vs Skor Ulasan")

        delivery_df = base_f.dropna(subset=[
            'order_delivered_customer_date',
            'order_estimated_delivery_date', 'review_score'
        ]).copy()
        delivery_df['delay_days'] = (
            delivery_df['order_delivered_customer_date'] -
            delivery_df['order_estimated_delivery_date']
        ).dt.days
        delivery_df['status_kirim'] = delivery_df['delay_days'].apply(
            lambda x: 'Terlambat' if x > 0 else 'Tepat/Lebih Cepat'
        )
        delay_score = (
            delivery_df.groupby('review_score')
            .agg(avg_delay=('delay_days', 'mean'),
                 pct_terlambat=('status_kirim', lambda x: (x == 'Terlambat').mean() * 100))
            .reset_index()
        )

        score_colors = sns.color_palette('muted', 5)
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        bars = axes[0].bar(delay_score['review_score'], delay_score['avg_delay'],
                           color=score_colors, edgecolor='white', width=0.6)
        axes[0].axhline(0, color='gray', linewidth=0.8, linestyle='--')
        for bar, val in zip(bars, delay_score['avg_delay']):
            offset = 0.3 if val >= 0 else -1.8
            axes[0].text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + offset, f'{val:.1f}d',
                         ha='center', fontsize=10, fontweight='bold')
        axes[0].set_title('Rata-rata Keterlambatan\nper Skor Ulasan', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Skor Ulasan')
        axes[0].set_ylabel('Rata-rata Hari')
        axes[0].set_xticks([1, 2, 3, 4, 5])
        axes[0].set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
        sns.despine(ax=axes[0])

        bars = axes[1].bar(delay_score['review_score'], delay_score['pct_terlambat'],
                           color=score_colors, edgecolor='white', width=0.6)
        for bar, val in zip(bars, delay_score['pct_terlambat']):
            axes[1].text(bar.get_x() + bar.get_width() / 2,
                         bar.get_height() + 0.5, f'{val:.1f}%',
                         ha='center', fontsize=10, fontweight='bold')
        axes[1].set_title('% Order Terlambat\nper Skor Ulasan', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Skor Ulasan')
        axes[1].set_ylabel('% Terlambat')
        axes[1].set_xticks([1, 2, 3, 4, 5])
        axes[1].set_xticklabels([f'⭐{s}' for s in [1, 2, 3, 4, 5]])
        sns.despine(ax=axes[1])

        plt.suptitle('Analisis Keterlambatan Pengiriman vs Skor Ulasan',
                     fontsize=13, fontweight='bold', y=1.02)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── TAB 3: Repeat Purchase ─────────────────
    with tab3:
        st.subheader("Repeat Purchase & Customer Retention")

        purchase_count = (
            base_f.groupby('customer_unique_id')['order_id']
            .nunique().reset_index()
            .rename(columns={'order_id': 'total_orders'})
        )
        purchase_count['tipe_pelanggan'] = purchase_count['total_orders'].apply(
            lambda x: 'One-time Buyer' if x == 1 else 'Repeat Buyer'
        )
        retention_rate = (purchase_count['tipe_pelanggan'] == 'Repeat Buyer').mean() * 100

        c1, c2, c3 = st.columns(3)
        c1.metric("Retention Rate",   f"{retention_rate:.1f}%")
        c2.metric("One-time Buyer",   f"{(purchase_count['tipe_pelanggan'] == 'One-time Buyer').sum():,}")
        c3.metric("Repeat Buyer",     f"{(purchase_count['tipe_pelanggan'] == 'Repeat Buyer').sum():,}")

        top_repeat_cat = (
            base_f
            .merge(purchase_count[['customer_unique_id', 'tipe_pelanggan']],
                   on='customer_unique_id', how='left')
            .merge(order_items_df[['order_id', 'product_id']], on='order_id', how='left')
            .merge(products_df[['product_id', 'product_category_name']],
                   on='product_id', how='left')
            .merge(category_df, on='product_category_name', how='left')
            .query("tipe_pelanggan == 'Repeat Buyer'")
            .groupby('product_category_name_english')['order_id']
            .nunique()
            .sort_values(ascending=False)
            .head(10).reset_index()
            .rename(columns={'order_id': 'n_orders',
                             'product_category_name_english': 'category'})
        )

        colors = sns.color_palette('muted', 2)
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))

        type_counts = purchase_count['tipe_pelanggan'].value_counts()
        axes[0].pie(type_counts, labels=type_counts.index, autopct='%1.1f%%',
                    colors=colors, explode=[0.05, 0], startangle=140)
        for at in [t for t in axes[0].texts if '%' in t.get_text()]:
            at.set_fontsize(10)
            at.set_fontweight('bold')
        axes[0].set_title(f'Komposisi Tipe Pelanggan\n(Retention Rate: {retention_rate:.1f}%)',
                          fontsize=12, fontweight='bold')

        bar_colors = sns.color_palette('muted', len(top_repeat_cat))
        bars = axes[1].barh(top_repeat_cat['category'][::-1],
                            top_repeat_cat['n_orders'][::-1],
                            color=bar_colors, edgecolor='white')
        for bar, val in zip(bars, top_repeat_cat['n_orders'][::-1]):
            axes[1].text(bar.get_width() + 5, bar.get_y() + bar.get_height() / 2,
                         f'{val:,}', va='center', fontsize=9, fontweight='bold')
        axes[1].set_xlabel('Jumlah Order', fontsize=11)
        axes[1].set_title('Top 10 Kategori — Repeat Buyer', fontsize=12, fontweight='bold')
        sns.despine(ax=axes[1])

        plt.suptitle('Repeat Purchase & Customer Retention',
                     fontsize=13, fontweight='bold', y=1.02)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── TAB 4: Geografis ───────────────────────
    with tab4:
        st.subheader("Distribusi Geografis Revenue per State")

        geo_revenue = (
            base_f.groupby('customer_state')
            .agg(total_revenue=('order_value', 'sum'),
                 n_orders=('order_id', 'count'),
                 avg_order_value=('order_value', 'mean'))
            .reset_index()
            .sort_values('total_revenue', ascending=False)
        )
        geo_revenue['revenue_share_%'] = (
            geo_revenue['total_revenue'] / geo_revenue['total_revenue'].sum() * 100
        ).round(2)

        n_state = st.slider("Tampilkan top N state", 5, len(geo_revenue), 10)
        top_geo = geo_revenue.head(n_state)
        top_avg = geo_revenue.nlargest(n_state, 'avg_order_value').sort_values('avg_order_value')

        fig, axes = plt.subplots(1, 2, figsize=(14, n_state * 0.5 + 1.5))
        colors = sns.color_palette('muted', n_state)

        bars = axes[0].barh(top_geo['customer_state'][::-1],
                            top_geo['total_revenue'][::-1] / 1_000,
                            color=colors, edgecolor='white')
        for bar, val in zip(bars, top_geo['total_revenue'][::-1] / 1_000):
            axes[0].text(bar.get_width() + 2, bar.get_y() + bar.get_height() / 2,
                         f'R${val:,.0f}K', va='center', fontsize=9, fontweight='bold')
        axes[0].set_xlabel('Total Revenue (Ribuan BRL)', fontsize=11)
        axes[0].set_title(f'Top {n_state} State — Total Revenue',
                          fontsize=12, fontweight='bold')
        axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}K'))
        sns.despine(ax=axes[0])

        bars = axes[1].barh(top_avg['customer_state'],
                            top_avg['avg_order_value'],
                            color=sns.color_palette('muted', len(top_avg)), edgecolor='white')
        for bar, val in zip(bars, top_avg['avg_order_value']):
            axes[1].text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                         f'R${val:,.0f}', va='center', fontsize=9, fontweight='bold')
        axes[1].set_xlabel('Rata-rata Nilai Order (BRL)', fontsize=11)
        axes[1].set_title(f'Top {n_state} State — Avg Nilai Order',
                          fontsize=12, fontweight='bold')
        axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'R${x:,.0f}'))
        sns.despine(ax=axes[1])

        plt.suptitle('Distribusi Geografis Revenue per State',
                     fontsize=13, fontweight='bold', y=1.02)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

        with st.expander("Lihat tabel lengkap"):
            st.dataframe(geo_revenue.reset_index(drop=True), use_container_width=True)
