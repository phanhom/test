"""角色动作状态机"""

from enum import Enum, auto


class PlayerState(Enum):
    IDLE = "idle"
    RUN = "run"
    JUMP = "jump"
    CROUCH = "crouch"
    SHOOT = "shoot"
    MELEE = "melee"
    DASH = "dash"
    HURT = "hurt"


class ActionStateMachine:
    """管理玩家动作状态：idle/run/jump/crouch/shoot/melee/dash/hurt"""

    def __init__(self):
        self.state = PlayerState.IDLE
        self.timer = 0
        self.dash_cooldown = 0
        self.melee_cooldown = 0

        # 可调参数
        self.dash_duration = 12
        self.melee_duration = 18
        self.dash_cooldown_total = 60
        self.melee_cooldown_total = 30

    def set_state(self, state: PlayerState):
        self.state = state
        self.timer = 0

    def can_act(self) -> bool:
        return self.state not in (PlayerState.HURT,)

    def can_dash(self) -> bool:
        return self.state != PlayerState.DASH and self.dash_cooldown <= 0

    def can_crouch(self) -> bool:
        return self.state in (PlayerState.IDLE, PlayerState.RUN)

    def handle_input(self, *, left=False, right=False, jump=False, crouch=False,
                     shoot=False, melee=False, dash=False, on_ground=True):
        """根据输入和当前状态转换状态。"""
        if self.state == PlayerState.HURT:
            return

        if self.state == PlayerState.DASH:
            return
        if self.state == PlayerState.MELEE:
            return

        # 跳跃状态由物理系统控制落地后恢复，输入不干预
        if self.state == PlayerState.JUMP:
            return

        if dash and self.can_dash():
            self.set_state(PlayerState.DASH)
            return

        if crouch and self.can_crouch():
            self.set_state(PlayerState.CROUCH)
            return

        if melee and self.melee_cooldown <= 0:
            self.set_state(PlayerState.MELEE)
            self.melee_cooldown = self.melee_cooldown_total
            return

        if shoot:
            self.set_state(PlayerState.SHOOT)
            return

        if not on_ground:
            self.set_state(PlayerState.JUMP)
            return

        if jump and on_ground:
            self.set_state(PlayerState.JUMP)
            return

        if left or right:
            self.set_state(PlayerState.RUN)
            return

        self.set_state(PlayerState.IDLE)

    def update(self):
        """每帧调用，处理计时和自动状态恢复。"""
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1

        if self.state in (PlayerState.DASH, PlayerState.MELEE, PlayerState.SHOOT, PlayerState.HURT):
            self.timer += 1

        if self.state == PlayerState.DASH and self.timer >= self.dash_duration:
            self.set_state(PlayerState.IDLE)
            self.dash_cooldown = self.dash_cooldown_total

        if self.state == PlayerState.MELEE and self.timer >= self.melee_duration:
            self.set_state(PlayerState.IDLE)

        if self.state == PlayerState.SHOOT and self.timer >= 6:
            self.set_state(PlayerState.IDLE)

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "timer": self.timer,
            "dash_cooldown": self.dash_cooldown,
            "melee_cooldown": self.melee_cooldown,
        }

    def from_dict(self, data: dict):
        self.state = PlayerState(data.get("state", "idle"))
        self.timer = data.get("timer", 0)
        self.dash_cooldown = data.get("dash_cooldown", 0)
        self.melee_cooldown = data.get("melee_cooldown", 0)
