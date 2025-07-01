"""
制約付きボトルネック最大化アルゴリズムの詳細検証テスト

各テストケースで利用可能な全ての経路オプション、そのボトルネック帯域、総遅延を明記し、
制約条件下でアルゴリズムが正しい経路を選択することを検証する。
"""

import networkx as nx
import pytest

from src.constrained_routing import calculate_path_metrics, constrained_max_load_path


def validate_constrained_path(
    G, source, target, path, max_delay, expected_bottleneck, expected_delay
):
    """
    制約付きボトルネック経路が正しいかを検証する。

    Parameters:
    -----------
    G : nx.Graph
        グラフ
    source : node
        開始ノード
    target : node
        終了ノード
    path : list
        検証する経路
    max_delay : float
        遅延制約
    expected_bottleneck : float
        期待されるボトルネック帯域
    expected_delay : float
        期待される総遅延
    """
    assert path[0] == source, f"経路の開始点が{source}であるべき"
    assert path[-1] == target, f"経路の終点が{target}であるべき"

    bottleneck, delay = calculate_path_metrics(G, path)

    assert delay <= max_delay, f"遅延制約違反: {delay}ms > {max_delay}ms"
    assert (
        bottleneck == expected_bottleneck
    ), f"期待ボトルネック {expected_bottleneck}Mbps だが、実際は {bottleneck}Mbps"
    assert (
        delay == expected_delay
    ), f"期待遅延 {expected_delay}ms だが、実際は {delay}ms"


class TestConstrainedMaxLoadPath:
    """制約付きボトルネック最大化の基本テスト"""

    def setup_method(self):
        """
        テスト用グラフをセットアップ。

        A から D への利用可能経路:

        1. **A → C → D**:
           - ボトルネック帯域: min(50, 70) = 50 Mbps
           - 総遅延: 5 + 4 = 9 ms

        2. **A → B → D**:
           - ボトルネック帯域: min(100, 80) = 80 Mbps
           - 総遅延: 10 + 3 = 13 ms

        3. **A → D** (直接):
           - ボトルネック帯域: 30 Mbps
           - 総遅延: 15 ms

        制約に応じて最適経路が変わることを検証する。
        """
        self.G = nx.Graph()
        self.G.add_edge("A", "B", weight=100, delay=10)  # 高帯域・高遅延
        self.G.add_edge("A", "C", weight=50, delay=5)  # 中帯域・低遅延
        self.G.add_edge("B", "D", weight=80, delay=3)  # 中帯域・低遅延
        self.G.add_edge("C", "D", weight=70, delay=4)  # 中帯域・低遅延
        self.G.add_edge("A", "D", weight=30, delay=15)  # 低帯域・高遅延（直接経路）

    def test_strict_delay_constraint_9ms(self):
        """
        制約: 9ms以下

        利用可能経路:
        - A → C → D: 9ms, 50Mbps ✓ (制約内)
        - A → B → D: 13ms, 80Mbps ✗ (制約超過)
        - A → D: 15ms, 30Mbps ✗ (制約超過)

        期待結果: A → C → D (唯一の制約内経路)
        """
        path = constrained_max_load_path(self.G, "A", "D", max_delay=9)
        validate_constrained_path(self.G, "A", "D", path, 9, 50, 9)
        assert path == ["A", "C", "D"]

    def test_moderate_delay_constraint_12ms(self):
        """
        制約: 12ms以下

        利用可能経路:
        - A → C → D: 9ms, 50Mbps ✓ (制約内)
        - A → B → D: 13ms, 80Mbps ✗ (制約超過)
        - A → D: 15ms, 30Mbps ✗ (制約超過)

        期待結果: A → C → D (制約内で唯一の経路)
        """
        path = constrained_max_load_path(self.G, "A", "D", max_delay=12)
        validate_constrained_path(self.G, "A", "D", path, 12, 50, 9)
        assert path == ["A", "C", "D"]

    def test_relaxed_delay_constraint_14ms(self):
        """
        制約: 14ms以下

        利用可能経路:
        - A → C → D: 9ms, 50Mbps ✓ (制約内)
        - A → B → D: 13ms, 80Mbps ✓ (制約内)
        - A → D: 15ms, 30Mbps ✗ (制約超過)

        期待結果: A → B → D (制約内で最大ボトルネック 80Mbps > 50Mbps)
        """
        path = constrained_max_load_path(self.G, "A", "D", max_delay=14)
        validate_constrained_path(self.G, "A", "D", path, 14, 80, 13)
        assert path == ["A", "B", "D"]

    def test_very_relaxed_constraint_20ms(self):
        """
        制約: 20ms以下

        利用可能経路:
        - A → C → D: 9ms, 50Mbps ✓ (制約内)
        - A → B → D: 13ms, 80Mbps ✓ (制約内)
        - A → D: 15ms, 30Mbps ✓ (制約内)

        期待結果: A → B → D (最大ボトルネック 80Mbps > 50Mbps > 30Mbps)
        """
        path = constrained_max_load_path(self.G, "A", "D", max_delay=20)
        validate_constrained_path(self.G, "A", "D", path, 20, 80, 13)
        assert path == ["A", "B", "D"]


class TestConstrainedMaxLoadPathComplex:
    """複数経路での制約付きボトルネック最大化テスト"""

    def setup_method(self):
        """
        より複雑なネットワークトポロジをセットアップ。

        S から T への利用可能経路:

        1. **S → A1 → A2 → T** (上側経路):
           - ボトルネック帯域: min(100, 90, 85) = 85 Mbps
           - 総遅延: 8 + 5 + 6 = 19 ms

        2. **S → B1 → B2 → T** (下側経路):
           - ボトルネック帯域: min(60, 55, 50) = 50 Mbps
           - 総遅延: 3 + 4 + 2 = 9 ms

        3. **S → C1 → C2 → C3 → T** (迂回路):
           - ボトルネック帯域: min(30, 25, 20, 15) = 15 Mbps
           - 総遅延: 1 + 1 + 1 + 1 = 4 ms

        4. **S → T** (直接経路):
           - ボトルネック帯域: 200 Mbps
           - 総遅延: 25 ms
        """
        self.G = nx.Graph()

        # 直接的な経路（高遅延・高帯域）
        self.G.add_edge("S", "T", weight=200, delay=25)

        # 上側経路（中遅延・高帯域）
        self.G.add_edge("S", "A1", weight=100, delay=8)
        self.G.add_edge("A1", "A2", weight=90, delay=5)
        self.G.add_edge("A2", "T", weight=85, delay=6)

        # 下側経路（低遅延・中帯域）
        self.G.add_edge("S", "B1", weight=60, delay=3)
        self.G.add_edge("B1", "B2", weight=55, delay=4)
        self.G.add_edge("B2", "T", weight=50, delay=2)

        # 迂回路（非常に低遅延・低帯域）
        self.G.add_edge("S", "C1", weight=30, delay=1)
        self.G.add_edge("C1", "C2", weight=25, delay=1)
        self.G.add_edge("C2", "C3", weight=20, delay=1)
        self.G.add_edge("C3", "T", weight=15, delay=1)

    def test_very_strict_constraint_5ms(self):
        """
        制約: 5ms以下

        利用可能経路:
        - S → A1 → A2 → T: 19ms ✗ (制約超過)
        - S → B1 → B2 → T: 9ms ✗ (制約超過)
        - S → C1 → C2 → C3 → T: 4ms, 15Mbps ✓ (制約内、唯一)
        - S → T: 25ms ✗ (制約超過)

        期待結果: S → C1 → C2 → C3 → T (制約内で唯一の経路)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=5)
        validate_constrained_path(self.G, "S", "T", path, 5, 15, 4)
        assert path == ["S", "C1", "C2", "C3", "T"]

    def test_moderate_constraint_10ms(self):
        """
        制約: 10ms以下

        利用可能経路:
        - S → A1 → A2 → T: 19ms ✗ (制約超過)
        - S → B1 → B2 → T: 9ms, 50Mbps ✓ (制約内)
        - S → C1 → C2 → C3 → T: 4ms, 15Mbps ✓ (制約内)
        - S → T: 25ms ✗ (制約超過)

        期待結果: S → B1 → B2 → T (制約内で最大ボトルネック 50Mbps > 15Mbps)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=10)
        validate_constrained_path(self.G, "S", "T", path, 10, 50, 9)
        assert path == ["S", "B1", "B2", "T"]

    def test_relaxed_constraint_20ms(self):
        """
        制約: 20ms以下

        利用可能経路:
        - S → A1 → A2 → T: 19ms, 85Mbps ✓ (制約内)
        - S → B1 → B2 → T: 9ms, 50Mbps ✓ (制約内)
        - S → C1 → C2 → C3 → T: 4ms, 15Mbps ✓ (制約内)
        - S → T: 25ms ✗ (制約超過)

        期待結果: S → A1 → A2 → T (制約内で最大ボトルネック 85Mbps > 50Mbps > 15Mbps)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=20)
        validate_constrained_path(self.G, "S", "T", path, 20, 85, 19)
        assert path == ["S", "A1", "A2", "T"]

    def test_no_constraint(self):
        """
        制約: なし (∞)

        利用可能経路:
        - S → A1 → A2 → T: 19ms, 85Mbps ✓
        - S → B1 → B2 → T: 9ms, 50Mbps ✓
        - S → C1 → C2 → C3 → T: 4ms, 15Mbps ✓
        - S → T: 25ms, 200Mbps ✓

        期待結果: S → T (最大ボトルネック 200Mbps)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=float("inf"))
        validate_constrained_path(self.G, "S", "T", path, float("inf"), 200, 25)
        assert path == ["S", "T"]


class TestConstrainedMaxLoadPathBoundary:
    """境界条件での制約付きボトルネック最大化テスト"""

    def setup_method(self):
        """
        境界値テスト用の精密なグラフをセットアップ。

        A から C への利用可能経路:

        1. **A → B → C**:
           - ボトルネック帯域: min(100, 80) = 80 Mbps
           - 総遅延: 5.0 + 5.0 = 10.0 ms (境界値)

        2. **A → D → C**:
           - ボトルネック帯域: min(70, 60) = 60 Mbps
           - 総遅延: 10.1 + 0.0 = 10.1 ms (境界を0.1ms超過)

        3. **A → E → C**:
           - ボトルネック帯域: min(50, 40) = 40 Mbps
           - 総遅延: 9.9 + 0.1 = 10.0 ms (境界値)

        10.0ms制約での境界動作を検証する。
        """
        self.G = nx.Graph()

        # 境界値ちょうどの経路1
        self.G.add_edge("A", "B", weight=100, delay=5.0)
        self.G.add_edge("B", "C", weight=80, delay=5.0)  # 合計10.0ms

        # 境界を超える経路
        self.G.add_edge("A", "D", weight=70, delay=10.1)  # 10.1ms (境界超過)
        self.G.add_edge("D", "C", weight=60, delay=0.0)  # 合計10.1ms

        # 境界値ちょうどの経路2 (ボトルネックは小さい)
        self.G.add_edge("A", "E", weight=50, delay=9.9)  # 9.9ms
        self.G.add_edge("E", "C", weight=40, delay=0.1)  # 合計10.0ms

    def test_exact_boundary_10_0ms(self):
        """
        制約: 10.0ms以下 (境界値ちょうど)

        利用可能経路:
        - A → B → C: 10.0ms, 80Mbps ✓ (境界値、ボトルネック大)
        - A → D → C: 10.1ms, 60Mbps ✗ (境界超過)
        - A → E → C: 10.0ms, 40Mbps ✓ (境界値、ボトルネック小)

        期待結果: A → B → C (境界内で最大ボトルネック 80Mbps > 40Mbps)
        """
        path = constrained_max_load_path(self.G, "A", "C", max_delay=10.0)
        validate_constrained_path(self.G, "A", "C", path, 10.0, 80, 10.0)
        assert path == ["A", "B", "C"]

    def test_just_over_boundary_10_1ms(self):
        """
        制約: 10.1ms以下 (境界をわずかに超える)

        利用可能経路:
        - A → B → C: 10.0ms, 80Mbps ✓ (制約内、ボトルネック大)
        - A → D → C: 10.1ms, 60Mbps ✓ (制約内、ボトルネック中)
        - A → E → C: 10.0ms, 40Mbps ✓ (制約内、ボトルネック小)

        期待結果: A → B → C (制約内で最大ボトルネック 80Mbps > 60Mbps > 40Mbps)
        """
        path = constrained_max_load_path(self.G, "A", "C", max_delay=10.1)
        validate_constrained_path(self.G, "A", "C", path, 10.1, 80, 10.0)
        assert path == ["A", "B", "C"]

    def test_just_under_boundary_9_9ms(self):
        """
        制約: 9.9ms以下 (境界をわずかに下回る)

        利用可能経路:
        - A → B → C: 10.0ms ✗ (制約超過)
        - A → D → C: 10.1ms ✗ (制約超過)
        - A → E → C: 10.0ms ✗ (制約超過)

        期待結果: 経路なし (NetworkXNoPath例外)
        """
        with pytest.raises(nx.NetworkXNoPath):
            constrained_max_load_path(self.G, "A", "C", max_delay=9.9)


class TestConstrainedMaxLoadPathOptimality:
    """最適性保証の検証テスト"""

    def setup_method(self):
        """
        最適性検証用の詳細なグラフをセットアップ。

        S から T への全6通りの経路:

        1. **S → L1A → L2A → T**:
           - ボトルネック: min(90, 85, 88) = 85 Mbps
           - 遅延: 2 + 3 + 4 = 9 ms

        2. **S → L1A → L2B → T**:
           - ボトルネック: min(90, 75, 92) = 75 Mbps
           - 遅延: 2 + 4 + 3 = 9 ms

        3. **S → L1B → L2B → T**:
           - ボトルネック: min(80, 95, 92) = 80 Mbps
           - 遅延: 3 + 2 + 3 = 8 ms

        4. **S → L1B → L2C → T**:
           - ボトルネック: min(80, 65, 55) = 55 Mbps
           - 遅延: 3 + 5 + 2 = 10 ms

        5. **S → L1C → L2C → T**:
           - ボトルネック: min(70, 60, 55) = 55 Mbps
           - 遅延: 4 + 3 + 2 = 9 ms
        """
        self.G = nx.Graph()

        # 第1層
        self.G.add_edge("S", "L1A", weight=90, delay=2)
        self.G.add_edge("S", "L1B", weight=80, delay=3)
        self.G.add_edge("S", "L1C", weight=70, delay=4)

        # 第2層
        self.G.add_edge("L1A", "L2A", weight=85, delay=3)
        self.G.add_edge("L1A", "L2B", weight=75, delay=4)
        self.G.add_edge("L1B", "L2B", weight=95, delay=2)
        self.G.add_edge("L1B", "L2C", weight=65, delay=5)
        self.G.add_edge("L1C", "L2C", weight=60, delay=3)

        # 第3層（終点）
        self.G.add_edge("L2A", "T", weight=88, delay=4)
        self.G.add_edge("L2B", "T", weight=92, delay=3)
        self.G.add_edge("L2C", "T", weight=55, delay=2)

    def test_constraint_8ms_optimal(self):
        """
        制約: 8ms以下

        利用可能経路:
        - S → L1B → L2B → T: 8ms, 80Mbps ✓ (制約内、唯一)
        - 他の全経路: 9-10ms ✗ (制約超過)

        期待結果: S → L1B → L2B → T (制約内で唯一の経路)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=8)
        validate_constrained_path(self.G, "S", "T", path, 8, 80, 8)
        assert path == ["S", "L1B", "L2B", "T"]

    def test_constraint_9ms_optimal(self):
        """
        制約: 9ms以下

        利用可能経路:
        - S → L1A → L2A → T: 9ms, 85Mbps ✓ (制約内、最大ボトルネック)
        - S → L1A → L2B → T: 9ms, 75Mbps ✓ (制約内)
        - S → L1B → L2B → T: 8ms, 80Mbps ✓ (制約内)
        - S → L1C → L2C → T: 9ms, 55Mbps ✓ (制約内)

        期待結果: S → L1A → L2A → T (制約内で最大ボトルネック 85Mbps)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=9)
        validate_constrained_path(self.G, "S", "T", path, 9, 85, 9)
        assert path == ["S", "L1A", "L2A", "T"]

    def test_constraint_10ms_optimal(self):
        """
        制約: 10ms以下

        利用可能経路:
        - S → L1A → L2A → T: 9ms, 85Mbps ✓ (制約内、最大ボトルネック)
        - S → L1A → L2B → T: 9ms, 75Mbps ✓ (制約内)
        - S → L1B → L2B → T: 8ms, 80Mbps ✓ (制約内)
        - S → L1B → L2C → T: 10ms, 55Mbps ✓ (制約内)
        - S → L1C → L2C → T: 9ms, 55Mbps ✓ (制約内)

        期待結果: S → L1A → L2A → T (制約内で最大ボトルネック 85Mbps)
        """
        path = constrained_max_load_path(self.G, "S", "T", max_delay=10)
        validate_constrained_path(self.G, "S", "T", path, 10, 85, 9)
        assert path == ["S", "L1A", "L2A", "T"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
