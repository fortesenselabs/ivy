import ivy
from collections import OrderedDict
import threading

import typing
import math

from .ivy__helpers import ivy_add
from .ivy__helpers import ivy_empty
from .ivy__helpers import ivy_linear
from .ivy__helpers import ivy_split


class ivy_Linear(ivy.Module):
    __constants__ = ["in_features", "out_features"]
    in_features: typing.Any
    out_features: typing.Any
    weight: typing.Any

    def __init__(arr, in_features, out_features, bias=True, device=None, dtype=None):
        factory_kwargs = {"device": device, "dtype": dtype}
        arr.super___init__(
            in_features,
            out_features,
            bias=bias,
            device=device,
            dtype=dtype,
            v=getattr(arr, "_v", None),
            buffers=getattr(arr, "_buffers", None),
            module_dict=getattr(arr, "_module_dict", None),
        )
        arr.in_features = in_features
        arr.out_features = out_features
        arr.weight = ivy.Array(ivy_empty((out_features, in_features), **factory_kwargs))
        if bias:
            arr.bias = ivy.Array(ivy_empty(out_features, **factory_kwargs))
        else:
            arr.register_parameter("bias", None)
        arr.reset_parameters()

    def reset_parameters(arr):
        Translated_kaiming_uniform_(arr.weight, a=math.sqrt(5))
        if arr.bias is not None:
            fan_in, _ = Translated__calculate_fan_in_and_fan_out(arr.weight)
            bound = 1 / math.sqrt(fan_in) if fan_in > 0 else 0
            Translated_uniform_(arr.bias, -bound, bound)

    def forward(arr, input):
        return ivy_linear(input, arr.weight, arr.bias)

    def extra_repr(arr):
        return f"in_features={arr.in_features}, out_features={arr.out_features}, bias={arr.bias is not None}"

    def super___init__(arr, *args, device=None, devices=None, **kwargs):
        super().__init__(
            arr,
            *args,
            device=device,
            devices=devices,
            training=True,
            build_mode="explicit",
            dynamic_backend=True,
            **kwargs,
        )
        super().__setattr__("_frontend_module", True)
        super().__setattr__(
            "_attr_mapping", {"_parameters": "v", "_modules": "module_dict"}
        )

    def __dir__(arr):
        module_attrs = dir(arr.__class__)
        attrs = list(arr.__dict__.keys())
        parameters = list(arr._v.keys())
        modules = list(arr._module_dict.keys())
        buffers = list(arr._buffers.keys())
        keys = module_attrs + attrs + parameters + modules + buffers
        keys = [key for key in keys if not key[0].isdigit()]
        return sorted(keys)

    def __getattribute__(arr, name):
        if name == "__dict__":
            return super().__getattribute__(name)
        if "_module_dict" in arr.__dict__:
            modules = arr.__dict__["_module_dict"]
            if name in modules:
                return modules[name]
        if "_buffers" in arr.__dict__:
            buffers = arr.__dict__["_buffers"]
            if name in buffers:
                return buffers[name]
        if "_v" in arr.__dict__:
            v = arr.__dict__["_v"]
            if name in v:
                return v[name]
        if "_attr_mapping" in arr.__dict__:
            mapping = arr.__dict__["_attr_mapping"]
            if name in mapping:
                return super().__getattribute__(mapping[name])
        return super().__getattribute__(name)

    def __getstate__(arr):
        state = arr.__dict__.copy()
        state.pop("_compiled_call_impl", None)
        state.pop("_thread_local", None)
        state.pop("_metrics_lock", None)
        return state

    def __repr__(arr):
        extra_lines = []
        extra_repr = arr._extra_repr()
        if extra_repr:
            extra_lines = ivy_split(extra_repr, "\n")
        child_lines = []
        for key, module in arr._module_dict.items():
            mod_str = repr(module)
            mod_str = arr._addindent(mod_str, 2)
            child_lines.append("(" + key + "): " + mod_str)
        lines = extra_lines + child_lines
        main_str = arr._get_name() + "("
        if lines:
            if len(extra_lines) == 1 and not child_lines:
                main_str += extra_lines[0]
            else:
                main_str += "\n  " + "\n  ".join(lines) + "\n"
        main_str += ")"
        return main_str

    def __setattr__(arr, name, value):
        def remove_from(*dicts_or_sets):
            for d in dicts_or_sets:
                if name in d:
                    if isinstance(d, dict):
                        del d[name]
                    else:
                        d.discard(name)

        params = arr.__dict__.get("_v")
        if params is not None and name in params and isinstance(value, Parameter):
            remove_from(arr.__dict__, arr._buffers, arr._module_dict)
            arr.register_parameter(name, value)
            super().__setattr__(name, value)
        else:
            super().__setattr__(name, value)

    def __setstate__(arr, state):
        state["_thread_local"] = threading.local()
        state["_metrics_lock"] = threading.Lock()
        arr.__dict__.update(state)

    def _build(arr, *args, **kwargs):
        for module in arr.__dict__.values():
            if isinstance(module, ivy.Module) and module is not arr:
                if not module._built:
                    module.build(
                        *module._args,
                        dynamic_backend=module._dynamic_backend,
                        **module._kwargs,
                    )
        return True

    def _call_impl(arr, *args, **kwargs):
        return arr.call(*args, **kwargs)

    def _create_variables(arr, device=None, dtype=None):
        v = ivy.Container(
            OrderedDict(
                [
                    (k.replace(".", "/"), v)
                    for k, v in arr.__dict__.items()
                    if isinstance(v, Parameter) and not k.startswith("_")
                ]
            )
        )
        v = (
            ivy.Container(
                OrderedDict(
                    {
                        _k.replace(".", "/"): _v
                        for _k, _v in arr._v.items()
                        if _k.replace(".", "/") not in v
                        and not isinstance(_v, ivy.Container)
                    },
                    **v,
                )
            )
            if arr._v
            else v
        )
        return v

    def _extra_repr(arr):
        return ""

    def _forward(arr, *a, **kw):
        ret = arr._call_impl(*a, **kw)
        return ret

    def _get_name(arr):
        return arr.__class__.__name__

    def _named_members(
        arr, get_members_fn, prefix="", recurse=True, remove_duplicate=True
    ):
        """Helper method for yielding various names + members of modules."""
        memo = set()
        modules = (
            arr.named_modules(prefix=prefix, remove_duplicate=remove_duplicate)
            if recurse
            else [(prefix, arr)]
        )
        for module_prefix, module in modules:
            members = get_members_fn(module)
            for k, v in members:
                if v is None or id(v) in memo:
                    continue
                if remove_duplicate:
                    ivy_add(memo, id(v))
                name = module_prefix + ("." if module_prefix else "") + k
                yield name, v

    def _replace_update_v(arr, new_v, native=None):
        from ivy.functional.ivy.gradients import _is_variable

        native = ivy.default(native, arr)
        for k, v in new_v.items():
            if isinstance(v, ivy.Container):
                native.module_dict[k] = arr._replace_update_v(v, native.module_dict[k])
            elif isinstance(v, Parameter):
                native.__setattr__(k, v)
            elif _is_variable(v):
                native.__setattr__(k, Parameter(v))
            elif isinstance(v, Tensor):
                native.__setattr__(k, Parameter(v, requires_grad=v.requires_grad))
            else:
                raise ivy.utils.exceptions.IvyException(
                    f"found item in variable container {v} which was neither a sub ivy.Container nor a variable."
                )
        return native

    def _update_v(arr, new_v, native=None):
        from ivy.functional.ivy.gradients import _is_variable

        native = ivy.default(native, arr)
        for k, v in new_v.items():
            if isinstance(v, ivy.Container):
                native.module_dict[k] = arr._replace_update_v(v, native.module_dict[k])
            elif isinstance(v, Parameter):
                native.__setattr__(k, v)
            elif _is_variable(v):
                native.__setattr__(k, Parameter(v))
            elif isinstance(v, Tensor):
                native.__setattr__(k, Parameter(v, requires_grad=v.requires_grad))
            else:
                raise ivy.utils.exceptions.IvyException(
                    f"found item in variable container {v} which was neither a sub ivy.Container nor a variable."
                )
        return native

    def add_module(arr, name, module):
        if not isinstance(module, ivy.Module) and module is not None:
            raise TypeError(f"{type(module)} is not a Module subclass")
        elif not isinstance(name, str):
            raise TypeError(f"module name should be a string. Got {type(name)}")
        elif hasattr(arr, name) and name not in arr._modules:
            raise KeyError(f"attribute '{name}' already exists")
        elif "." in name:
            raise KeyError(f'module name can\'t contain ".", got: {name}')
        elif name == "":
            raise KeyError('module name can\'t be empty string ""')
        arr._modules[name] = module
        super().__setattr__(name, module)

    def apply(arr, fn):
        for module in arr.children():
            if hasattr(module, "apply"):
                module.apply(fn)
            else:
                fn(module)
        fn(arr)
        return arr

    def children(arr):
        for _, module in arr.named_children():
            yield module

    def get_parameter(arr, target):
        target = target.replace(".", "/")
        return arr.v[target]

    def get_submodule(arr, target):
        if target == "":
            return arr
        atoms: typing.Any = ivy_split(target, ".")
        mod: typing.Any = arr
        for item in atoms:
            if not hasattr(mod, item):
                raise AttributeError(
                    mod._get_name() + " has no attribute `" + item + "`"
                )
            mod = getattr(mod, item)
            if not isinstance(mod, ivy.Module):
                raise TypeError("`" + item + "` is not an nn.Module")
        return mod

    def modules(arr):
        for _, module in arr.named_modules():
            yield module

    def named_buffers(arr, prefix="", recurse=True, remove_duplicate=True):
        if not getattr(arr, "_built", False):
            arr.build(*arr._args, dynamic_backend=arr._dynamic_backend, **arr._kwargs)
        gen = arr._named_members(
            lambda module: module.buffers.items(),
            prefix=prefix,
            recurse=recurse,
            remove_duplicate=remove_duplicate,
        )
        yield from gen

    def named_children(arr):
        if not getattr(arr, "_built", False):
            arr.build(*arr._args, dynamic_backend=arr._dynamic_backend, **arr._kwargs)
        memo = set()
        for name, module in arr._module_dict.items():
            if module is not None and id(module) not in memo:
                ivy_add(memo, id(module))
                yield name, module

    def named_modules(arr, memo=None, prefix="", remove_duplicate=True):
        if not getattr(arr, "_built", False):
            arr.build(*arr._args, dynamic_backend=arr._dynamic_backend, **arr._kwargs)
        if memo is None:
            memo = set()
        if id(arr) not in memo:
            if remove_duplicate:
                ivy_add(memo, id(arr))
            yield prefix, arr
            for name, module in arr._module_dict.items():
                if module is None:
                    continue
                submodule_prefix = prefix + ("." if prefix else "") + name
                if not hasattr(module, "named_modules"):
                    yield submodule_prefix, arr
                else:
                    yield from module.named_modules(
                        memo, submodule_prefix, remove_duplicate
                    )

    def named_parameters(arr, prefix="", recurse=True, remove_duplicate=True):
        if not getattr(arr, "_built", False):
            arr.build(*arr._args, dynamic_backend=arr._dynamic_backend, **arr._kwargs)
        gen = arr._named_members(
            lambda module: module.v.items(),
            prefix=prefix,
            recurse=recurse,
            remove_duplicate=remove_duplicate,
        )
        yield from gen

    def parameters(arr, recurse=True):
        for _, param in arr.named_parameters(recurse=recurse):
            yield param

    def register_buffer(arr, name, value, persistent=False):
        super().register_buffer(name, value)

    def register_module(arr, name, module):
        """Alias for :func:`add_module`."""
        arr.add_module(name, module)

    def register_parameter(arr, name, value):
        super().register_parameter(name, value)

    def requires_grad_(arr, requires_grad=True):
        for p in arr.parameters():
            p.requires_grad_(requires_grad)
        return arr
