import os
import json
from enum import Enum
import requests
import time
from typing import Callable
from litellm.utils import ModelResponse
import torch
from transformers import AutoTokenizer
from petals import AutoDistributedModelForCausalLM


class PetalsError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(
            self.message
        )  # Call the base class constructor with the parameters it needs

def completion(
    model: str,
    messages: list,
    model_response: ModelResponse,
    print_verbose: Callable,
    encoding,
    logging_obj,
    optional_params=None,
    stream=False,
    litellm_params=None,
    logger_fn=None,
):
    
    model = model

    # You could also use "meta-llama/Llama-2-70b-chat-hf" or any other supported model from 🤗 Model Hub

    tokenizer = AutoTokenizer.from_pretrained(model, use_fast=False, add_bos_token=False)
    model = AutoDistributedModelForCausalLM.from_pretrained(model)
    model = model.cuda()

    prompt = ""
    for message in messages:
        if "role" in message:
            if message["role"] == "user":
                prompt += (
                    f"{message['content']}"
                )
            else:
                prompt += (
                    f"{message['content']}"
                )
        else:
            prompt += f"{message['content']}"
    

    ## LOGGING
    logging_obj.pre_call(
            input=prompt,
            api_key="",
            additional_args={"complete_input_dict": optional_params},
        )
    
    ## COMPLETION CALL
    inputs = tokenizer(prompt, return_tensors="pt")["input_ids"].cuda()
    outputs = model.generate(inputs, max_new_tokens=5)
    print(outputs)


    ## LOGGING
    logging_obj.post_call(
            input=prompt,
            api_key="",
            original_response=outputs,
            additional_args={"complete_input_dict": optional_params},
        )
    print_verbose(f"raw model_response: {outputs}")
    ## RESPONSE OBJECT
    output_text = tokenizer.decode(outputs[0])
    model_response["choices"][0]["message"]["content"] = output_text

    ## CALCULATING USAGE - baseten charges on time, not tokens - have some mapping of cost here. 
    prompt_tokens = len(
        encoding.encode(prompt)
    ) 
    completion_tokens = len(
        encoding.encode(model_response["choices"][0]["message"]["content"])
    )

    model_response["created"] = time.time()
    model_response["model"] = model
    model_response["usage"] = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }
    return model_response

def embedding():
    # logic for parsing in - calling - parsing out model embedding calls
    pass