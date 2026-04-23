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
"""Abstract capability tags a task may require.

A capability names a category of tool (e.g. reading a file, running code)
without naming any specific tool. Harness adapters translate capabilities into
concrete tool names.
"""

from __future__ import annotations

from enum import Enum


class Capability(str, Enum):
    FILESYSTEM_READ = "filesystem_read"
    FILESYSTEM_WRITE = "filesystem_write"
    TERMINAL = "terminal"
    CODE_EXECUTE = "code_execute"
    WEB_SEARCH = "web_search"
    SCHEDULE_TASK = "schedule_task"
    SEND_MESSAGE = "send_message"
    MEMORY_PERSIST = "memory_persist"
    SKILL_INVOKE = "skill_invoke"
    TODO_TRACK = "todo_track"
    CLARIFY = "clarify"
