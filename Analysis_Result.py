import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
from matplotlib import patheffects

class AnalysisResult:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def analyze_transaction_patterns(self, transactions, min_support=0.1, min_confidence=0.5):
        df = pd.DataFrame(transactions)

        # Split produk into lists of items
        df['produk'] = df['produk'].apply(lambda x: x.split(', '))

        # Encode transaction data
        te = TransactionEncoder()
        te_ary = te.fit_transform(df['produk'])
        df_encoded = pd.DataFrame(te_ary, columns=te.columns_)

        # Generate frequent itemsets
        frequent_itemsets = apriori(df_encoded, min_support=min_support, use_colnames=True)

        if frequent_itemsets.empty:
            return {'error': 'Tidak ditemukan pola asosiasi yang memenuhi kriteria minimum support dan confidence.'}

        # Generate association rules
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

        if rules.empty:
            return {'error': 'Tidak ditemukan pola asosiasi yang memenuhi kriteria minimum support dan confidence.'}

        # Process and round values in rules
        rules['antecedents'] = rules['antecedents'].apply(lambda x: list(x))
        rules['consequents'] = rules['consequents'].apply(lambda x: list(x))
        rules['support'] = rules['support'].apply(self.round_to_four_decimals)
        rules['confidence'] = rules['confidence'].apply(self.round_to_four_decimals)
        rules['lift'] = rules['lift'].apply(self.round_to_four_decimals)

        # Sort rules by confidence and lift in descending order
        sorted_rules = rules.sort_values(by=['confidence', 'lift'], ascending=[False, False])

        # Generate business insights
        insights = [
            f"• Pelanggan yang membeli {rule['antecedents']} "
            f"cenderung juga membeli {rule['consequents']} "
            f"dengan confidence {rule['confidence']} dan lift {rule['lift']}."
            for _, rule in sorted_rules.iterrows()
        ]

        # Prepare results
        pola_asosiasi = sorted_rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].to_dict(orient='records')

        results = {
            'pola_asosiasi': pola_asosiasi,
            'insight_bisnis': insights,
            'item_supports': df_encoded.mean().sort_values(ascending=False).apply(self.round_to_four_decimals).to_dict(),
            'two_itemsets': [],
            'three_itemsets': []
        }

        # Extract 2-itemsets and 3-itemsets
        for _, row in frequent_itemsets.iterrows():
            if len(row['itemsets']) == 2:
                results['two_itemsets'].append({'itemsets': list(row['itemsets']), 'support': self.round_to_four_decimals(row['support'])})
            elif len(row['itemsets']) == 3:
                results['three_itemsets'].append({'itemsets': list(row['itemsets']), 'support': self.round_to_four_decimals(row['support'])})

        # Generate bar chart for visualization
        plot_url = self.create_bar_chart(pola_asosiasi, min_support, min_confidence)
        results['plot_url'] = plot_url

        return results

    def create_bar_chart(self, rules, min_support, min_confidence):
        antecedents = [', '.join(rule['antecedents']) for rule in rules]
        consequents = [', '.join(rule['consequents']) for rule in rules]
        confidence = [rule['confidence'] for rule in rules]
        lift = [rule['lift'] for rule in rules]

        combined_labels = [f"{ante} → {con}" for ante, con in zip(antecedents, consequents)]
        num_rules = len(combined_labels)

        fig_width = 20
        fig_height = max(6, num_rules * 0.85)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        y_pos = np.arange(num_rules)
        bar_width = 0.35

        color_conf = plt.cm.Blues(0.6)
        color_lift = plt.cm.Oranges(0.6)

        bars1 = ax.barh(y_pos - bar_width/2, confidence, height=bar_width, color=color_conf, label='Confidence', alpha=0.85, edgecolor='darkblue')
        bars2 = ax.barh(y_pos + bar_width/2, lift, height=bar_width, color=color_lift, label='Lift', alpha=0.85, edgecolor='darkorange')

        ax.set_ylabel('Pola Asosiasi', fontweight='bold', fontsize=16, color='#34495e')
        ax.set_xlabel('Confidence dan Lift', fontweight='bold', fontsize=16, color='#34495e')
        ax.set_title(f'Diagram Pola Asosiasi: Confidence and Lift\n'
                     f'Min Support: {min_support}, Min Confidence: {min_confidence}', 
                     fontweight='bold', fontsize=18, color='#2c3e50', pad=20)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(combined_labels, ha='right', fontsize=14, color='#2c3e50', rotation=0)

        for bar in bars1 + bars2:
            xval = bar.get_width()
            formatted_value = f"{xval:.4f}" if not xval.is_integer() else f"{xval:.1f}"
            ax.text(xval + 0.05, bar.get_y() + bar.get_height() / 2, formatted_value,
                    ha='left', va='center', fontsize=12, color='black', weight='bold',
                    path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])

        ax.xaxis.grid(True, linestyle='--', alpha=0.5, color='gray')
        max_x = max(max(confidence), max(lift))
        ax.set_xlim(0, max_x * 1.3)
        ax.margins(y=0.1)

        legend = ax.legend(loc='upper right', fontsize=14, frameon=True, facecolor='white', edgecolor='gray', fancybox=True)
        for text in legend.get_texts():
            text.set_fontweight('bold')

        plt.tight_layout(pad=3)

        img = BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        return plot_url

    @staticmethod
    def round_to_four_decimals(x):
        return round(x, 4)

