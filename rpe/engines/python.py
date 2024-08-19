# Copyright 2019 The resource-policy-evaluation-library Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import importlib.util
import inspect
import sys

from dataclasses import asdict

from rpe.policy import Evaluation, EvaluationResult, Policy


class PythonPolicyEngine:
    counter = 0

    def __init__(self, package_path):
        self._policies = {}
        self.package_path = package_path
        PythonPolicyEngine.counter += 1
        self.package_name = "rpe.plugins.policies.py_" + str(PythonPolicyEngine.counter)

        self._load_policies()

    def _load_policies(self):
        spec = importlib.util.spec_from_file_location(
            self.package_name, "{}/__init__.py".format(self.package_path)
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[self.package_name] = module

        spec.loader.exec_module(module)

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and hasattr(obj, "applies_to")
                and isinstance(obj.applies_to, list)
            ):
                self._policies[name] = obj

    def policies(self):
        """
        Returns:
            A list of names of configured policies
        """

        policies = [
            Policy(
                policy_id=policy_name,
                engine=self,
                applies_to=policy_cls.applies_to,
                description=policy_cls.description,
                policy_attributes=getattr(policy_cls, "policy_attributes", {}),
            )
            for policy_name, policy_cls in self._policies.items()
        ]

        return policies

    def evaluate(self, resource):
        matched_policies = dict(
            filter(
                lambda policy: resource.type() in policy[1].applies_to,
                self._policies.items(),
            )
        )

        # Loop over policy and build evals, so we can catch exceptions

        evals = []

        for policy_name, policy_cls in matched_policies.items():
            try:
                if hasattr(policy_cls, "should_evaluate_policy"):
                    should_evaluate_policy_res = policy_cls.should_evaluate_policy(
                        resource
                    )
                    if not should_evaluate_policy_res:
                        print(
                            f"Policy: {policy_name}, will not be evaluated for resource {resource} "
                            f"as should_evaluate_policy returned {should_evaluate_policy_res}"
                        )
                        continue

                if hasattr(policy_cls, "evaluate"):
                    eval_result = policy_cls.evaluate(resource)
                    if not isinstance(eval_result, EvaluationResult):
                        raise ValueError(
                            'Python policy "evaluate" function must return an EvaluationResult object'
                        )

                    full_eval = Evaluation(
                        resource=resource,
                        engine=self,
                        policy_id=policy_name,
                        **asdict(eval_result),
                    )
                    evals.append(full_eval)

                else:
                    evals.append(self._legacy_eval(resource, policy_name, policy_cls))

            # These are user-provided modules, we need to catch any exception
            except Exception as e:
                print(f"Evaluation exception. Policy: {policy_name}, Message: {str(e)}")

        return evals

    def _legacy_eval(self, resource, policy_name, policy_cls):
        compliant = policy_cls.compliant(resource) is True

        eval_attr = {"excluded": policy_cls.excluded(resource) is True}

        ev = Evaluation(
            resource=resource,
            engine=self,
            policy_id=policy_name,
            compliant=compliant,
            remediable=hasattr(policy_cls, "remediate"),
            evaluation_attributes=eval_attr,
        )

        return ev

    def remediate(self, resource, policy_id):
        policy_cls = self._policies[policy_id]
        policy_cls.remediate(resource)
