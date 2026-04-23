# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Hermes harness adapter: capability -> Hermes tool name(s).

Declares the mapping only; does not run the harness. Tool surface reference:
the `hermes-agent` bundle's tool registry (terminal, file, read_file, process,
execute_code, skills, todo, patch, web_search, schedule, send_message,
memory). Lists are ordered by preference (most specific first).
"""

from __future__ import annotations

from resources_servers.harness_bench.capabilities import Capability


CAPABILITY_TO_TOOLS: dict[Capability, list[str]] = {
    Capability.FILESYSTEM_READ: ["read_file", "file"],
    Capability.FILESYSTEM_WRITE: ["file", "patch"],
    Capability.TERMINAL: ["terminal", "process"],
    Capability.CODE_EXECUTE: ["execute_code", "terminal"],
    Capability.WEB_SEARCH: ["web_search"],
    Capability.SCHEDULE_TASK: ["schedule"],
    Capability.SEND_MESSAGE: ["send_message"],
    Capability.MEMORY_PERSIST: ["memory"],
    Capability.SKILL_INVOKE: ["skills"],
    Capability.TODO_TRACK: ["todo"],
    Capability.CLARIFY: ["clarify"],
}
