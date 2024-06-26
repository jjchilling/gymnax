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
    """
    2D Semi-Circle Point Robot environment similar to Dorfman et al. 2021
    https://openreview.net/pdf?id=IBdEfhLveS
    """

    def __init__(self):
        super().__init__()

    @property
    def default_params(self) -> EnvParams:
        # Default environment parameters
        return EnvParams()
    

    def step_env(self, key: chex.PRNGKey, state: EnvState, action: chex.Array, params: EnvParams):
        """Steps through the environment using the given action and updates the state."""
        print("YOU GOTTA BE HERE")
        # Clip the action to ensure it's within the max force limits
        a = jnp.clip(action, -params.max_force, params.max_force)
        new_pos = state.pos + a

        print("state_pos")
        print(state.pos)
        print("\n")
        print("new_pos")
        print(new_pos)
        print("\n")

        # Compute the new and old distances to the goal
        new_goal_distance = jnp.linalg.norm(new_pos - state.goal)
        old_goal_distance = jnp.linalg.norm(state.pos - state.goal)

        print("goal_distance")
        print(new_goal_distance)
        print("\n")

        # Determine if the goal is reached
        goal_reached = new_goal_distance <= params.goal_radius

        # Reward function to use if the goal is reached
        def reward_if_goal_reached(_):
            return 100.0  # High reward for reaching the goal

        # Adjusted reward function when the goal is not reached
        def reward_if_not_reached(_):
            # Reward is based on the improvement in distance towards the goal
            distance_improvement = old_goal_distance - new_goal_distance
            return jax.lax.max(distance_improvement * 10, -1.0)  # Scale improvement and set a floor for the reward

        # Use lax.cond to conditionally compute the reward
        reward = lax.cond(
            goal_reached,
            reward_if_goal_reached,
            reward_if_not_reached,
            None
        )

        # Update position depending on whether the goal is reached
        def update_position_if_reached(_):
            # Sample a new starting position if the goal is reached
            return sample_agent_position(key, params.circle_radius, params.center_init)

        def update_position_if_not_reached(_):
            # Maintain the new position if the goal is not reached
            return new_pos

        # Conditionally update the position
        new_pos = lax.cond(
            goal_reached,
            update_position_if_reached,
            update_position_if_not_reached,
            None
        )

        # Update the count of goals reached
        new_goals_reached = state.goals_reached + jnp.where(goal_reached, 1, 0)

        # Update the state
        new_state = EnvState(
            last_action=a,
            last_reward=reward,
            pos=new_pos,
            goal=state.goal,
            goals_reached=new_goals_reached,
            time=state.time + 1
        )

        # Determine if the episode is done
        done = self.is_terminal(new_state, params)

        # Return the observation, new state, reward, done status, and discount factor
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
        """Reset environment state by sampling initial position."""
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
        """Concatenate reward, one-hot action and time stamp."""
        time_rep = jax.lax.select(
            params.normalize_time, time_normalization(state.time), state.time
        )
        return jnp.hstack(
            [state.pos, state.last_reward, state.last_action, time_rep]
        )

    def is_terminal(self, state: EnvState, params: EnvParams) -> bool:
        """Check whether state is terminal."""
        # Check number of steps in episode termination condition
        done = state.time >= params.max_steps_in_episode
        return done

    @property
    def name(self) -> str:
        """Environment name."""
        return "PointRobot-misc"

    @property
    def num_actions(self) -> int:
        """Number of actions possible in environment."""
        return 2

    def action_space(self, params: Optional[EnvParams] = None) -> spaces.Box:
        """Action space of the environment."""
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
        """Observation space of the environment."""
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
        """State space of the environment."""
        return spaces.Dict(
            {
                "last_action": spaces.Discrete(self.num_actions),
                "last_reward": spaces.Discrete(2),
                "time": spaces.Discrete(params.max_steps_in_episode),
            }
        )

    def render(self, state: EnvState, params: EnvParams):
        """Small utility for plotting the agent's state."""
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
    """Normalize time integer into range given max time."""
    return (max_lim - min_lim) * t / t_max + min_lim


def sample_agent_position(
    key: chex.PRNGKey, circle_radius: float, center_init: bool
) -> chex.Array:
    """Sample a random position in circle (or set position to center)."""
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
