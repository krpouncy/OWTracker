"""This module contains custom transformers for the Overwatch 2 dataset."""

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

class FeatureScaler(BaseEstimator, TransformerMixin):
    def __init__(self, features_to_scale=None):
        if features_to_scale is None:
            self.features_to_scale = ['K', 'A', 'D', 'Damage', 'H', 'MIT']
        else:
            self.features_to_scale = features_to_scale

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        for feature in self.features_to_scale:
            X[feature] = X[feature] / X['Time']
        return X

class CappingFeatureValues(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Cap K, A, D, Damage, H, MIT based on PlayerID
        X['K'] = X['K'].clip(upper=5)
        X['A'] = X['A'].clip(upper=4)
        X['D'] = X['D'].clip(upper=3)
        X['Damage'] = X['Damage'].clip(upper=2500)

        # Cap H based on PlayerID
        X.loc[X['PlayerID'] == 0, 'H'] = X.loc[X['PlayerID'] == 0, 'H'].clip(upper=600)
        X.loc[X['PlayerID'].isin([1, 2]), 'H'] = X.loc[X['PlayerID'].isin([1, 2]), 'H'].clip(upper=400)
        X.loc[X['PlayerID'] == 3, 'H'] = X.loc[X['PlayerID'] == 3, 'H'].clip(upper=2500)
        # If PlayerID >3, handle accordingly if needed

        X['MIT'] = X['MIT'].clip(upper=2500)
        return X

class FeatureResetter(BaseEstimator, TransformerMixin):
    def __init__(self, features_to_reset=None):
        if features_to_reset is None:
            self.features_to_reset = ['K', 'A', 'D', 'Damage', 'H', 'MIT']
        else:
            self.features_to_reset = features_to_reset

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()
        for feature in self.features_to_reset:
            X[feature] = X[feature] * X['Time']
        return X

class DataPivoter(BaseEstimator, TransformerMixin):
    def __init__(self, player_features=None):
        if player_features is None:
            self.player_features = ['K', 'A', 'D', 'Damage', 'H', 'MIT']
        else:
            self.player_features = player_features

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Pivot the data
        X = X.copy()
        cleaned_data = X.pivot_table(
            index=['SnapID'],
            columns='PlayerID',
            values=self.player_features
        )
        cleaned_data.columns = [f"{feature}_player{int(player)}" for feature, player in cleaned_data.columns]
        cleaned_data = cleaned_data.reset_index()
        cleaned_data = cleaned_data.drop(columns=['SnapID'], errors='ignore')
        cleaned_data = cleaned_data.fillna(0)
        return cleaned_data

class FeatureEngineer(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = X.copy()

        # Feature Engineering: tank_ratio and support_ratio
        X['tank_ratio'] = X['K_player0'] / (X['K_player0'] + np.sqrt(X['MIT_player0'] + 1e-6))
        X['support_ratio'] = (X['Damage_player3'] + X['Damage_player4']) / (
            X['Damage_player3'] + X['Damage_player4'] +
            X['H_player3'] + X['H_player4'] + 1e-6
        )

        # Define tank_status
        conditions_tank = [
            (X['tank_ratio'] <= 0.05),
            (X['tank_ratio'] < 0.08)
        ]
        choices_tank = ['poor', 'average']
        X['tank_status'] = np.select(conditions_tank, choices_tank, default='good')

        # Define support_status
        conditions_support = [
            (X['support_ratio'] < 0.14),
            (X['support_ratio'] <= 0.32)
        ]
        choices_support = ['poor', 'average']
        X['support_status'] = np.select(conditions_support, choices_support, default='good')

        X = X.drop(columns=['tank_ratio', 'support_ratio'], errors='ignore')

        # Remove specific columns
        columns_to_drop = [
            'Damage_player0', 'MIT_player0', 'MIT_player1', 'MIT_player2', 'MIT_player3', 'MIT_player4'
        ]
        X = X.drop(columns=columns_to_drop, errors='ignore')

        # Combine Damage, Assists, and Support Healing
        X['A_dps'] = X['A_player1'] + X['A_player2']
        X['A_support'] = X['A_player3'] + X['A_player4']
        X['Damage_support'] = X['Damage_player3'] + X['Damage_player4']
        X['Damage_dps'] = X['Damage_player3'] + X['Damage_player4']  # Note: Same as Damage_support?
        columns_to_drop_combined = [
            'A_player1', 'A_player2', 'A_player3', 'A_player4',
            'Damage_player1', 'Damage_player2', 'Damage_player3', 'Damage_player4'
        ]
        X = X.drop(columns=columns_to_drop_combined, errors='ignore')

        return X

class FinalDataCleaner(BaseEstimator, TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Example: Drop any remaining unwanted columns
        # Modify as needed
        return X