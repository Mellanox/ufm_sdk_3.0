import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-bright',
  templateUrl: './bright.component.html',
  styleUrls: ['./bright.component.scss']
})
export class BrightComponent implements OnInit {

  constructor(private router: Router,
              private activatedRoute: ActivatedRoute) { }

  ngOnInit(): void {
  }

}
