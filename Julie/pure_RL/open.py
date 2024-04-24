from openai import OpenAI

client = OpenAI(api_key="")

message_with_code = """

Reaching the goal is perfect. Just movie in a rectangluar motion before reaching the goal. One rectangle please.
DO NOT USE IF STATEMENTS please jax jit everything.
    @staticmethod
    def discount(state: EnvState, params: EnvParams):
        
        def if_not_terminal(_):
            return 0.99

        def if_terminal(_):
            return 0.0

        is_not_terminal = state.time <= params.max_steps_in_episode
        return lax.cond(is_not_terminal, if_not_terminal, if_terminal, None)

    def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
       
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        goal_distance = jnp.linalg.norm(new_pos - state.goal)
        goal_reached = goal_distance <= params.goal_radius

        def reward_goal_reached(_):
            return 100.0  # High reward if goal is reached

        def reward_not_reached(_):
            # Soft penalties as before but without leaving the bounds
            width_penalty = jnp.square(jnp.maximum(0, jnp.abs(new_pos[0] - state.goal[0]) - params.circle_radius))
            height_penalty = jnp.square(jnp.maximum(0, jnp.abs(new_pos[1] - state.goal[1] + params.circle_radius / 2) - params.circle_radius / 2))
            return - (width_penalty + height_penalty)

        reward = lax.cond(goal_reached, reward_goal_reached, reward_not_reached, None)

        def update_pos_reached(_):
            return state.goal  # if reached, perhaps reset or stick to the goal

        def update_pos_not_reached(_):
            return new_pos  # continue with new position

        new_pos = lax.cond(goal_reached, update_pos_reached, update_pos_not_reached, None)

        new_goals_reached = state.goals_reached + goal_reached
        new_time = state.time + 1

        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=new_time
        )

        done = new_state.time > params.max_steps_in_episode

        return self.get_obs(new_state, params), new_state, reward, done, {"discount": self.discount(new_state, params)} 

    

PREVIOUS:
    def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
      
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        goal_distance = jnp.linalg.norm(new_pos - state.goal)
        goal_reached = goal_distance <= params.goal_radius

        rect_width = 2 * params.circle_radius
        rect_height = params.circle_radius
        center_x = state.goal[0]
        center_y = state.goal[1] + rect_height / 2

        # Check bounds within the rectangle
        dist_from_center_x = jnp.abs(new_pos[0] - center_x) - rect_width / 2
        dist_from_center_y = jnp.abs(new_pos[1] - center_y) - rect_height / 2
        
        out_of_bounds_penalty_x = lax.max(0.0, dist_from_center_x)
        out_of_bounds_penalty_y = lax.max(0.0, dist_from_center_y)
        
        penalty = out_of_bounds_penalty_x**2 + out_of_bounds_penalty_y**2
        
        def reward_goal_reached(_):
            return 100.0
        
        def reward_not_reached(_):
            return -penalty
        
        reward = lax.cond(goal_reached, reward_goal_reached, reward_not_reached, None)

        new_goals_reached = state.goals_reached + goal_reached
        new_time = state.time + 1

        def update_pos_reached(_):
            return state.goal
        
        def update_pos_not_reached(_):
            return new_pos
        
        new_pos = lax.cond(goal_reached, update_pos_reached, update_pos_not_reached, None)
        
        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=new_time
        )

        done = new_state.time > params.max_steps_in_episode

        return self.get_obs(new_state, params), new_state, reward, done, {"discount": self.discount(new_state, params)}

    def discount(self, state: EnvState, params: EnvParams):
        # Implement logic to determine discount factor
        return 0.99 if not self.is_terminal(state, params) else 0.0
        # HEREEEEEE


PREVIOUS: (LEAVES SCREEN...)

def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
        
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        goal_distance = jnp.linalg.norm(new_pos - state.goal)
        goal_reached = goal_distance <= params.goal_radius

        # Vertical displacement computed as a fraction of the number of goals reached
        vertical_displacement = state.goals_reached * 0.05
        def rectangular_trajectory_reward(new_pos, state, vertical_displacement, params):
            # Use the same rectangle definitions but add the vertical displacement
            rect_width = 2 * params.circle_radius
            rect_height = params.circle_radius
            
            # Adjust goal_center to account for the vertical displacement
            goal_center = state.goal + jnp.array([0, vertical_displacement])

            width_dist = jnp.abs(new_pos[0] - goal_center[0])  # Distance along x-axis from goal
            height_dist = jnp.abs(new_pos[1] - goal_center[1])  # Distance along y-axis from goal

            # Soft penalties for deviating from the rectangle path
            width_penalty = jnp.square(jnp.maximum(0, width_dist - rect_width / 2))
            height_penalty = jnp.square(jnp.maximum(0, height_dist - rect_height / 2))

            return - (width_penalty + height_penalty)

        def reward_if_goal_reached(_):
            return 100.0

        def reward_if_not_reached(_):
            return rectangular_trajectory_reward(new_pos, state, vertical_displacement, params)

        reward = lax.cond(
            goal_reached,
            reward_if_goal_reached,
            reward_if_not_reached,
            None
        )

        def update_position_if_reached(_):
            return sample_agent_position(key, params.circle_radius, params.center_init)

        def update_position_if_not_reached(_):
            return new_pos

        new_pos = lax.cond(
            goal_reached,
            update_position_if_reached,
            update_position_if_not_reached,
            None
        )

        new_goals_reached = state.goals_reached + jnp.where(goal_reached, 1, 0)

        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=state.time + 1
        )

        done = self.is_terminal(new_state, params)

        return (
            lax.stop_gradient(self.get_obs(new_state, params)),
            lax.stop_gradient(new_state),
            reward,
            done,
            {"discount": self.discount(new_state, params)}
        ) 


PREVIOUS:
def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        goal_distance = jnp.linalg.norm(new_pos - state.goal)
        goal_reached = goal_distance <= params.goal_radius

        def rectangular_trajectory_reward(new_pos, state, params):
            # Ideally define your rectangle's widths and heights, assuming based around the goal as center
            rect_width = 2 * params.circle_radius
            rect_height = params.circle_radius

            goal_center = state.goal
            width_dist = jnp.abs(new_pos[0] - goal_center[0])  # Distance along x-axis from goal
            height_dist = jnp.abs(new_pos[1] - goal_center[1])  # Distance along y-axis from goal

            # Introduce soft penalties for deviating from the rectangle path
            width_penalty = jnp.square(jnp.maximum(0, width_dist - rect_width / 2))
            height_penalty = jnp.square(jnp.maximum(0, height_dist - rect_height / 2))

            return - (width_penalty + height_penalty)

        def reward_if_goal_reached(_):
            return 100.0

        def reward_if_not_reached(_):
            return rectangular_trajectory_reward(new_pos, state, params)

        reward = lax.cond(
            goal_reached,
            reward_if_goal_reached,
            reward_if_not_reached,
            None
        )

        def update_position_if_reached(_):
            return sample_agent_position(key, params.circle_radius, params.center_init)

        def update_position_if_not_reached(_):
            return new_pos

        new_pos = lax.cond(
            goal_reached,
            update_position_if_reached,
            update_position_if_not_reached,
            None
        )

        new_goals_reached = state.goals_reached + jnp.where(goal_reached, 1, 0)

        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=state.time + 1
        )

        done = self.is_terminal(new_state, params)

        return (
            lax.stop_gradient(self.get_obs(new_state, params)),
            lax.stop_gradient(new_state),
            reward,
            done,
            {"discount": self.discount(new_state, params)}
        )

PREVIOUS QUERY:

To provide context, my params are already trained to reach the goal. I just want the trajectory of my model to be preserved while it relatively moves in a rectangular motion. Can you try modifying my reward function:


  def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):       
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        goal_distance = jnp.linalg.norm(new_pos - state.goal)
  
        goal_reached = goal_distance <= params.goal_radius

        def reward_if_goal_reached(_):
            return 100.0

        def reward_if_not_reached(_):
            return -goal_distance

        reward = lax.cond(
            goal_reached,
            reward_if_goal_reached,
            reward_if_not_reached,
            None
        )

        def update_position_if_reached(_):
            return sample_agent_position(key, params.circle_radius, params.center_init)

        def update_position_if_not_reached(_):
            return new_pos

        new_pos = lax.cond(
            goal_reached,
            update_position_if_reached,
            update_position_if_not_reached,
            None
        )

        # Properly convert the boolean to an integer using JAX's operations
        new_goals_reached = state.goals_reached + jnp.where(goal_reached, 1, 0)

        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=state.time + 1
        )

        done = self.is_terminal(new_state, params)

        return (
            lax.stop_gradient(self.get_obs(new_state, params)),
            lax.stop_gradient(new_state),
            reward,
            done,
            {"discount": self.discount(new_state, params)}
        )

        For my enviornment Point Robot on Gymnax:

        import jax
import jax.numpy as jnp
from jax import lax
from gymnax.environments import environment, spaces
from typing import Tuple, Optional
import chex
from flax import struct



@struct.dataclass
class EnvState:
    last_action: chex.Array
    last_reward: float
    pos: chex.Array
    goal: chex.Array
    goals_reached: int
    time: float


@struct.dataclass
class EnvParams:
    max_force: float = 0.1  # Max action (+/-)
    circle_radius: float = 1.0  # Radius of semi-circle
    dense_reward: bool = False  # Distance reward at each timestep
    goal_radius: float = 0.2  # Radius for success
    center_init: bool = False  # Init at [0, 0]. Otherwise sample in radius
    normalize_time: bool = True  # Normalize timestep into [-1, 1]
    max_steps_in_episode: int = 100  # Steps in an episode (constant goal)


class PointRobot(environment.Environment):

    2D Semi-Circle Point Robot environment similar to Dorfman et al. 2021
    https://openreview.net/pdf?id=IBdEfhLveS
    
    def __init__(self):
        super().__init__()

    @property
    def default_params(self) -> EnvParams:
        # Default environment parameters
        return EnvParams()
    

    def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
     

        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a
  
        goal_distance = jnp.linalg.norm(new_pos - state.goal)

        goal_reached = goal_distance <= params.goal_radius

        def reward_if_goal_reached(_):
            return 100.0

        def reward_if_not_reached(_):
            return -goal_distance

        reward = lax.cond(
            goal_reached,
            reward_if_goal_reached,
            reward_if_not_reached,
            None
        )

        def update_position_if_reached(_):
            return sample_agent_position(key, params.circle_radius, params.center_init)

        def update_position_if_not_reached(_):
            return new_pos

        new_pos = lax.cond(
            goal_reached,
            update_position_if_reached,
            update_position_if_not_reached,
            None
        )

        # Properly convert the boolean to an integer using JAX's operations
        new_goals_reached = state.goals_reached + jnp.where(goal_reached, 1, 0)

        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=state.time + 1
        )

        done = self.is_terminal(new_state, params)

        return (
            lax.stop_gradient(self.get_obs(new_state, params)),
            lax.stop_gradient(new_state),
            reward,
            done,
            {"discount": self.discount(new_state, params)}
        )

    
        ORIGINAL

    def reset_env(
        self, key: chex.PRNGKey, params: EnvParams
    ) -> Tuple[chex.Array, EnvState]:
     
        # Sample reward function + construct state as concat with timestamp
        rng_goal, rng_pos = jax.random.split(key)
        angle = jax.random.uniform(rng_goal, minval=0, maxval=jnp.pi)
        xs = params.circle_radius * jnp.cos(angle)
        ys = params.circle_radius * jnp.sin(angle)
        goal = jnp.array([xs, ys])
        sampled_pos = sample_agent_position(
            rng_pos, params.circle_radius, params.center_init
        )

        state = EnvState(
            jnp.zeros(2),
            0.0,
            sampled_pos,
            goal,
            0,
            0.0,
        )
        return self.get_obs(state, params), state

    def get_obs(self, state: EnvState, params: EnvParams) -> chex.Array:
      
        time_rep = jax.lax.select(
            params.normalize_time, time_normalization(state.time), state.time
        )
        return jnp.hstack(
            [state.pos, state.last_reward, state.last_action, time_rep]
        )

    def is_terminal(self, state: EnvState, params: EnvParams) -> bool:
    
        # Check number of steps in episode termination condition
        done = state.time >= params.max_steps_in_episode
        return done

    @property
    def name(self) -> str:

        return "PointRobot-misc"

    @property
    def num_actions(self) -> int:

        return 2

    def action_space(self, params: Optional[EnvParams] = None) -> spaces.Box:

        if params is None:
            params = self.default_params
        low = jnp.array(
            [-params.max_force, -params.max_force], dtype=jnp.float32
        )
        high = jnp.array(
            [params.max_force, params.max_force], dtype=jnp.float32
        )
        return spaces.Box(low, high, (2,), jnp.float32)

    def observation_space(self, params: EnvParams) -> spaces.Box:

        low = jnp.array(
            6 * [-jnp.finfo(jnp.float32).max],
            dtype=jnp.float32,
        )
        high = jnp.array(
            6 * [jnp.finfo(jnp.float32).max],
            dtype=jnp.float32,
        )
        return spaces.Box(low, high, (6,), jnp.float32)

    def state_space(self, params: EnvParams) -> spaces.Dict:

        return spaces.Dict(
            {
                "last_action": spaces.Discrete(self.num_actions),
                "last_reward": spaces.Discrete(2),
                "time": spaces.Discrete(params.max_steps_in_episode),
            }
        )

    def render(self, state: EnvState, params: EnvParams):
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        angles = jnp.linspace(0, jnp.pi, 100)
        x, y = jnp.cos(angles), jnp.sin(angles)
        ax.plot(x, y, color="k")
        plt.axis("scaled")
        ax.set_xlim(-1.25, 1.25)
        ax.set_ylim(-0.25, 1.25)
        ax.set_xticks([])
        ax.set_yticks([])

        circle = plt.Circle(
            (state.goal[0], state.goal[1]), radius=params.goal_radius, alpha=0.3
        )
        ax.add_artist(circle)

        circle = plt.Circle(
            (state.pos[0], state.pos[1]), radius=0.05, alpha=1, color="red"
        )
        ax.add_artist(circle)
        return fig, ax
    


def time_normalization(
    t: float, min_lim: float = -1.0, max_lim: float = 1.0, t_max: int = 100
) -> float:
    return (max_lim - min_lim) * t / t_max + min_lim


def sample_agent_position(
    key: chex.PRNGKey, circle_radius: float, center_init: bool
) -> chex.Array:
    rng_radius, rng_angle = jax.random.split(key)
    sampled_radius = jax.random.uniform(
        rng_radius, minval=0, maxval=circle_radius
    )
    sampled_angle = jax.random.uniform(rng_angle, minval=0, maxval=jnp.pi)

    pos = jax.lax.select(
        center_init,
        jnp.zeros(2),
        jnp.array(
            [
                sampled_radius * jnp.cos(sampled_angle),
                sampled_radius * jnp.sin(sampled_angle),
            ]
        ),
    )
    return pos

"""



# create a chat completion
chat_completion = client.chat.completions.create(model="gpt-4-turbo", messages=[{"role": "user", "content": message_with_code}])

# print the chat completion
print(chat_completion.choices[0].message.content)